#include <sys/types.h>
#include <unistd.h>
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>

#define BUFSIZE 1024

const char* logfile = "./log";
int logfd, pipefd_in[2], pipefd_out[2];

void exit_func()
{
	close(logfd);
	close(pipefd_in[1]);
	close(pipefd_out[0]);
	exit(0);
}

void thread_read()
{
	char buffer[BUFSIZE];
	while(1)
	{
		int nbytes = read(0,buffer,BUFSIZE);
		if(nbytes < 0)
			exit_func();
		write(logfd,buffer,nbytes);
		write(pipefd_in[1],buffer,nbytes);
	}
}


void thread_write()
{
	char buffer[BUFSIZE];
	while(1)
	{
		int nbytes = read(pipefd_out[0],buffer,BUFSIZE);
		if(nbytes < 0)
			exit_func();
		write(1,buffer,nbytes);
	}
} 

int main(int argc, char** argv)
{
	if (argc < 2)
	{
		fprintf(stdout,"Usage: binary file\n");
		exit(1);
	}

	setvbuf(stdin,0,2,0);
	setvbuf(stdout,0,2,0);
	setvbuf(stderr,0,2,0);

	logfd = open(logfile, O_WRONLY | O_CREAT | O_APPEND, S_IRUSR | S_IWUSR);

	if(pipe(pipefd_out) < 0)
	{
		fprintf(stderr,"[!] Error pipe\n");
		exit(1);
	}
	if(pipe(pipefd_in) < 0)
	{
		fprintf(stderr,"[!] Error pipe\n");
		exit(1);
	}

	pid_t pid = fork();
	if(pid < 0)
	{
		fprintf(stderr,"[!] Error fork\n");
		exit(1);
	}
	else if(pid == 0)
	{
		//child process
		close(pipefd_in[1]);
		close(pipefd_out[0]);
		dup2(pipefd_in[0],0);
		dup2(pipefd_out[1],1);
		execl(argv[1],argv[1],NULL);
		fprintf(stderr,"[!] Error execl\n");
		abort();
	}
	//parent process
	signal(SIGCHLD,exit_func);
	close(pipefd_in[0]);
	close(pipefd_out[1]);

	pthread_t thread1, thread2;

	pthread_create(&thread1,0,(void*)thread_read,0);
	pthread_create(&thread2,0,(void*)thread_write,0);

	pthread_join(thread1,0);
	pthread_join(thread2,0);

	exit_func();

	return 0;
}
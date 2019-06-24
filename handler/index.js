var app = require('express')(),
	bodyParser = require('body-parser');

const PORT = 4869;
//------

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
	extended: true
}));

//----------

app.use((req, res, next) => {
	res.set('Access-Control-Allow-Origin', '*');
	next();
});

//--------


app.get('/', (req, res) => {

	var flag = req.query.flag;
	if (flag) {
		console.log(flag);
	}
	res.send('OK');
})









//------

app.listen(PORT, () => {
	console.log('Listening on %d...', PORT);
});
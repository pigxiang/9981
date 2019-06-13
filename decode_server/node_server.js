const url = require('url');
const http = require('http');

const decode = require('./decoder.js').decode;

const app = http.createServer(function (request, response) {
    let rslt = '';
    try {
        const query = url.parse(request.url, true).query;
        const a1 = query.a1;
        const a2 = query.a2;
        rslt = decode(a1, a2)
        console.log(rslt)
    } catch (e) {

    }
    response.writeHead(200, {"Content-Type": "text/html"});
    response.write(rslt);
    response.end();
});

console.log("start!!!!")
app.listen(3000);
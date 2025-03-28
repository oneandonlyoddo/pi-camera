const express = require('express')
const fs = require("fs");
const app = express()
const port = 3000
const staticFolder = "./static";

if (!fs.existsSync(staticFolder)){
    fs.mkdirSync(staticFolder);
}


app.use("/img", express.static(staticFolder));

app.set('view engine', 'pug');

app.get('/', (req, res) => {
    fs.readdir(staticFolder, (err, files) => {
        paths = [];
        for(let file of files) {
            path = "./img/" + file;
            paths.push(path);
        }
        res.render('index', {
            title: 'local gallery',
            files: paths
        });
    });   
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
});


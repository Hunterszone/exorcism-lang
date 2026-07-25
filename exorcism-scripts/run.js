const fs = require('fs');
const path = require('path');
const wasmFile = path.join(__dirname, 'MyLanguageProgram.wasm');
const wasmBuffer = fs.readFileSync(wasmFile);

WebAssembly.instantiate(wasmBuffer, {
    env: { print_value_to_terminal: (val) => console.log(val) }
}).then(obj => {
    obj.instance.exports.main();
}).catch(err => console.error(err));

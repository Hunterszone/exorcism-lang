# EXORCISM LANG 

The written code is compiled into a cross-platform WebAssembly binary (.wasm), which runs natively via a tiny Node.js script.


## HOW TO COMPILE & RUN - COMMANDS

### Clear the containing output dir
```console
del /f /q *.ll *.wasm run.js              
```

### Compile
```console
py compiler.py 							 
```

### Run the executable program"# exorcism-lang" 
```console
node run.js 								 
```
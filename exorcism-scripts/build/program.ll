; ModuleID = "MiniCompilerModule"
target triple = "unknown-unknown-unknown"
target datalayout = ""

declare void @"print_string"(i8* %".1")

declare void @"print_int"(i32 %".1")

define i32 @"main"()
{
entry:
  %".2" = bitcast [12 x i8]* @"str_3" to i8*
  call void @"print_string"(i8* %".2")
  %"add_call" = call i32 @"add"(i32 5, i32 6)
  call void @"print_int"(i32 %"add_call")
  ret i32 0
}

@"str_3" = constant [12 x i8] c"Hello World\00"
define i32 @"add"(i32 %"a", i32 %"b")
{
entry:
  %"a.1" = alloca i32
  store i32 %"a", i32* %"a.1"
  %"b.1" = alloca i32
  store i32 %"b", i32* %"b.1"
  %"loadtmp" = load i32, i32* %"a.1"
  %"loadtmp.1" = load i32, i32* %"b.1"
  %"addtmp" = add i32 %"loadtmp", %"loadtmp.1"
  ret i32 %"addtmp"
}

!wasm.memory = !{  }
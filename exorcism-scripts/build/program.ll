; ModuleID = "MiniCompilerModule"
target triple = "unknown-unknown-unknown"
target datalayout = ""

declare void @"print_string"(i8* %".1")

define i32 @"main"()
{
entry:
  %".2" = bitcast [13 x i8]* @"hello_string" to i8*
  call void @"print_string"(i8* %".2")
  ret i32 0
}

@"hello_string" = constant [13 x i8] c"Hello World!\00"
!wasm.memory = !{  }
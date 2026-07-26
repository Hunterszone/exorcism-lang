; ModuleID = "MiniCompilerModule"
target triple = "unknown-unknown-unknown"
target datalayout = ""

declare void @"print_string"(i8* %".1")

define i32 @"main"()
{
entry:
  ret i32 0
}

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
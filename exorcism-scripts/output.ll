; ModuleID = "javx_core_module"
target triple = "wasm32-unknown-unknown"
target datalayout = ""

declare void @"print_value_to_terminal"(i32 %".1")

define i32 @"main"()
{
entry:
  %"myNumber" = alloca i32
  %"addtmp" = add i32 40, 2
  store i32 %"addtmp", i32* %"myNumber"
  %"loaded" = load i32, i32* %"myNumber"
  call void @"print_value_to_terminal"(i32 %"loaded")
  ret i32 0
}

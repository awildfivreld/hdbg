import bdb
import functools
from dataclasses import dataclass
from enum import Enum
from pprint import pprint
from types import FrameType
import linecache
from typing import Any, Iterator, Dict, Literal, Union, List

from colored import fg, bg  # type: ignore


@dataclass
class LineType:
    filename: str
    line_no: int
    line: str
    caller_name: str

    locals: Dict[str, Any]

    type: Literal["line"] = "line"

    def format_locals(self):
        return f"{fg('dark_green')}locals: ("+",".join([f"{k}={v}" for k,v in self.locals.items() if k[0] != '_' and not callable(v)]) + ")"

    def format(self, indent):
        return f"{fg('yellow')} {self.line_no: <3}" + " "*indent + f"{fg('green')} LINE: {fg('blue')}{self.line[:-1].strip()}  {self.format_locals()}", indent


@dataclass
class CallType:
    filename: str
    line_no: int
    method_name: str

    arguments: Dict[str, Any]

    type: Literal["call"] = "call"

    def format_arguments(self):
        return f"{fg('red')}("+",".join(f"{k}={v}" for k,v in self.arguments.items()) + ")"

    def format(self, indent):
        return f"{fg('yellow')} {self.line_no: <3}" + " "*indent + f"{fg('magenta')} CALL: {self.method_name}{self.format_arguments()}", indent+2

@dataclass
class ReturnType:
    filename: str
    line_no: int
    method_name: str
    return_value: Any

    type: Literal["return"] = "return"

    def format(self, indent):
        indent -= 2
        return f"{fg('yellow')} {self.line_no: <3}" + " "*indent + f"{fg('purple_3')} RET : {self.method_name} {fg('red')} ({self.return_value})", indent

Types = Union[CallType, LineType, ReturnType]

class CustomDebugger(bdb.Bdb):
    history: List[Types]

    def __init__(self):
        super().__init__()

        self.history = []

    def user_line(self, frame: FrameType) -> None:
        name = frame.f_code.co_name
        if not name: name = '???'
        fn = self.canonic(frame.f_code.co_filename)
        if "hdbg" in fn:
            line = linecache.getline(fn, frame.f_lineno, frame.f_globals)

            dump_line = LineType(filename=frame.f_code.co_filename, line_no=frame.f_lineno, line=line, caller_name=name, locals={k:v for k,v in frame.f_locals.items() if k[0] != "_"})
            self.history.append(dump_line)

    def user_call(self, frame: FrameType, argument_list) -> None:
        if "hdbg" in frame.f_code.co_filename:
            name = frame.f_code.co_name

            if name in ("<listcomp>", "<dictcomp>"):
                dot0content = list(frame.f_locals[".0"])
                frame.f_locals[".0"] = iter(dot0content)

                args = {".0": dot0content}
            else:
                args = {arg_name: frame.f_locals.get(arg_name) for arg_name in frame.f_code.co_varnames}


            dump_call = CallType(filename=frame.f_code.co_filename, line_no=frame.f_lineno, method_name=name, arguments=args)
            self.history.append(dump_call)



    def user_return(self, frame: FrameType, return_value: Any) -> None:
        if "hdbg" in frame.f_code.co_filename:
            dump_return = ReturnType(filename=frame.f_code.co_filename, line_no=frame.f_lineno, method_name=frame.f_code.co_name, return_value=return_value)
            self.history.append(dump_return)


print("starting...")
debugger = CustomDebugger()
debugger.run("import examplecode")

current_indent = 0
for action in debugger.history:
    txt, indent = action.format(current_indent)
    current_indent = indent
    print(txt)


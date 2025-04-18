from typing import Callable, TypeVar, Any, Dict, Optional
import inspect

from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.delta_generator import DeltaGenerator

from langchain_core.callbacks.base import BaseCallbackHandler
import streamlit as st


def get_streamlit_cb(parent_container: DeltaGenerator) -> BaseCallbackHandler:
    class StreamHandler(BaseCallbackHandler):
        def __init__(
            self, container: st.delta_generator.DeltaGenerator, initial_text: str = ""
        ):
            self.container = container
            self.thoughts_placeholder = self.container.container()
            self.tool_output_placeholder = None
            self.token_placeholder = self.container.empty()
            self.text = initial_text

        def on_llm_new_token(self, token: str, **kwargs) -> None:
            self.text += token
            self.token_placeholder.write(self.text)

        def on_tool_start(
            self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
        ) -> None:
            with self.thoughts_placeholder:
                status_placeholder = st.empty()
                with status_placeholder.status(
                    "Consultando herramienta...", expanded=True
                ) as s:
                    st.write("Herramienta llamada -> ", serialized["name"])
                    st.write("Descripción: ", serialized["description"])
                    st.write("Entrada herramienta: ")
                    st.code(input_str)
                    st.write("Salida herramienta: ")
                    self.tool_output_placeholder = st.empty()
                    s.update(label="Llamada a herramienta completa!", expanded=False)

        def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
            if self.tool_output_placeholder:
                self.tool_output_placeholder.code(output.content)

    fn_return_type = TypeVar("fn_return_type")

    def add_streamlit_context(
        fn: Callable[..., fn_return_type],
    ) -> Callable[..., fn_return_type]:
        ctx = get_script_run_ctx()

        def wrapper(*args, **kwargs) -> fn_return_type:
            add_script_run_ctx(ctx=ctx)
            return fn(*args, **kwargs)

        return wrapper

    st_cb = StreamHandler(parent_container)

    for method_name, method_func in inspect.getmembers(
        st_cb, predicate=inspect.ismethod
    ):
        if method_name.startswith("on_"):
            setattr(st_cb, method_name, add_streamlit_context(method_func))

    return st_cb

"""English prompts for the bundled decision assistant."""
from typing import Any, Dict
def _base(instruction:str,question:str)->str:return f"You are a decision-support assistant. Do not decide for the user. Surface assumptions, blind spots, conflicts, missing information, uncertainty, and reflection questions. Return valid JSON only.\nQuestion: {question}\n{instruction}"
def rational(question:str,values:Dict[str,int])->str:return _base('Compare benefits, risks, opportunity costs, reversibility, values, and second-order effects.',question)
def random(question:str)->str:return _base('Return six concrete options as a reflection exercise; randomness is not evidence.',question)
def nature(question:str,weather_ctx:Dict[str,Any])->str:return _base(f'Use this environmental context only as an alternative perspective: {weather_ctx}.',question)
def dialogue(question:str)->str:return _base('Ask one high-value reflective question and give three possible responses.',question)
def fengshui(question:str,bazi:Any=None)->str:return _base(f'Give a clearly labeled traditional-culture perspective only. Context: {bazi}',question)

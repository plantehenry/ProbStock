from Pred import *

from abc import ABC, abstractmethod

# must check for erros and if error throw 1
class Logic(ABC):

    @abstractmethod 
    def get_pct(self, preds: list[Pred]) -> float:
        pass


class BasicOne(Logic):

    def __init__(self, logic_vars: list) -> None:
        super().__init__()

    def get_pct(self, preds: list[Pred]) -> float:
        try:
            return preds[0] * 10
        except:
            return 0
    
class AlwaysZero(Logic):

    def __init__(self, logic_vars: list) -> None:
        super().__init__()

    def get_pct(self, preds: list[Pred]) -> float:
        return 0
        

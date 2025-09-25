from pydantic import BaseModel, Field
from typing import List

class ExportOption(BaseModel):
    file_phan_tich: str
    nam: int
    bien_can_xuat: List[str]

class ExportRequest(BaseModel):
    lua_chon_xuat: List[ExportOption] = Field(
        ..., description="List of export options, each option corresponds to one sheet."
    )

from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UnitCreate(BaseModel):
    name : str | None = None 
    short_name : str | None = None 
    description : str | None = None 
    is_active : bool | None = None 
    display_order : int |None = None

class UnitUpdate(BaseModel):
    name : str | None = None 
    short_name : str | None = None 
    description : str | None = None 
    is_active : bool | None = None 
    display_order : int |None = None

class UnitResponse(BaseModel):
    id: int 
    name : str
    short_name : str  
    description : str  
    is_active : bool  
    display_order : int 
    created_at : datetime
    updated_at : datetime

    model_config = ConfigDict(from_attributes=True)
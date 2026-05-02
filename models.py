from pydantic import BaseModel, EmailStr

class RegistrationCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    university: str
    department: str
    semester: str
    experience: str
    motivation: str

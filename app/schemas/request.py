# models for request validation , so whatever stuff is incoming to the application gets validated
# before the data hits the pipeline
# TODO add in middleware for prompt injection 

from pydantic import BaseModel, Field, field_validator
from typing import Literal

class UserInput(BaseModel) :
    # there gonna be 6 fields - scholarship name, type of program (enum), goal (one liner) , resume points (cpuld be an entire text field)
    scholarship_name: str = Field(
        ...,
        min_length=1,
        max_length=200, 
        description= "Name of the scholarship"
    )

    program_type: Literal[
        "Undergrad",
        "Graduate",
        "Research",
        "Community Leadership",
        "PHD",
        "Other" 
    ] = Field(
        ...,
        description="Type of program"
    )

    goal_one_liner:str = Field(
        ...,
        min_length=10,
        max_length=500,
        description= "One sentence goal or story"
    )
    resume_points : list[str] = Field(
        ...,
        min_length=2,
        description="list of resume bullet points"
    )

# this is gonna be the validator for the resume points field
    @field_validator('resume_points')
    @classmethod
    # args as the resume points (v)
    def validate_resume_points(cls, v):
        # for i (postion of bullet point in the list provided), point in enumerate (going through the list)
        for i, point in enumerate(v):
            # so an empty string is python is basically false, and a not makes it false again, so overallif the condition is true (not + false)
            if not point.strip():
                raise ValueError(
                    f"Resume point {i+1} cannot be empty"
                )
                return v 

    

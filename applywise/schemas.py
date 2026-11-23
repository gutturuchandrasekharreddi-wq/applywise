"""Validated API input and output shapes."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

Status = Literal["saved", "applied", "interview", "offer", "rejected", "withdrawn"]


class ApplicationFields(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=160)
    status: Status = "saved"
    location: str | None = Field(default=None, max_length=120)
    job_url: HttpUrl | None = None
    source: str | None = Field(default=None, max_length=100)
    salary: str | None = Field(default=None, max_length=100)
    applied_on: date | None = None
    follow_up_on: date | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ApplicationCreate(ApplicationFields):
    pass


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, min_length=1, max_length=160)
    status: Status | None = None
    location: str | None = Field(default=None, max_length=120)
    job_url: HttpUrl | None = None
    source: str | None = Field(default=None, max_length=100)
    salary: str | None = Field(default=None, max_length=100)
    applied_on: date | None = None
    follow_up_on: date | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ApplicationRead(ApplicationFields):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class MatchRequest(BaseModel):
    resume_text: str = Field(min_length=30, max_length=30000)
    job_description: str = Field(min_length=30, max_length=30000)


class MatchResult(BaseModel):
    score: int
    matched_terms: list[str]
    missing_terms: list[str]
    resume_terms: list[str]
    job_terms: list[str]

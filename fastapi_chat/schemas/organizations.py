from typing import Optional, Text

import uuid_utils as uuid
from pydantic import BaseModel, ConfigDict, Field


class Organization(BaseModel):
    id: Text = Field(..., description="Organization ID in UUID Version 7 format")
    name: Text = Field(..., description="Organization name")
    description: Optional[Text] = Field(default=None)
    owner_id: Text = Field(..., description="The initial admin user's ID")
    disabled: bool = Field(default=False)


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: Text = Field(..., description="Organization name")
    description: Optional[Text] = Field(default=None)
    disabled: bool = Field(default=False)

    def to_organization(
        self, *, organization_id: Optional[Text] = None, owner_id: Text
    ) -> Organization:
        return Organization.model_validate(
            {
                "id": organization_id or str(uuid.uuid7()),
                "name": self.name,
                "description": self.description,
                "owner_id": owner_id,
                "disabled": self.disabled,
            }
        )


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: Optional[Text] = Field(default=None, description="Organization name")
    description: Optional[Text] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)

    def apply_organization(self, organization: Organization) -> Organization:
        organization_data = organization.model_dump()
        organization_data.update(
            self.model_dump(exclude_none=True, exclude={"id", "owner_id"})
        )
        return Organization.model_validate(organization_data)

from __future__ import annotations

from dataclasses import dataclass, fields
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.db.models import CredentialSource, LLMCredential
from src.infoservice.errors import NotFound


@dataclass(frozen=True, slots=True)
class CreateCredential:
    provider: str
    model: str
    ciphertext: bytes
    key_mask: str
    base_url: str | None = None
    credential_source: CredentialSource = CredentialSource.USER


class CredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_owned(self, credential_id: UUID, user_id: UUID) -> LLMCredential:
        stmt = select(LLMCredential).where(LLMCredential.id == credential_id, LLMCredential.user_id == user_id)
        credential = (await self.session.execute(stmt)).scalar_one_or_none()
        if credential is None:
            raise NotFound("Ключ не найден")
        return credential

    async def upsert(self, user_id: UUID, data: CreateCredential) -> LLMCredential:
        stmt = select(LLMCredential).where(LLMCredential.user_id == user_id, LLMCredential.provider == data.provider)
        credential = (await self.session.execute(stmt)).scalar_one_or_none()
        values = {field.name: getattr(data, field.name) for field in fields(data)}
        if credential is None:
            credential = LLMCredential(user_id=user_id, **values)
            self.session.add(credential)
        else:
            for name, value in values.items():
                setattr(credential, name, value)
        await self.session.flush()
        return credential

    async def delete(self, credential_id: UUID, user_id: UUID) -> None:
        credential = await self.get_owned(credential_id, user_id)
        await self.session.delete(credential)
        await self.session.flush()

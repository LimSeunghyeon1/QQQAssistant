from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.domain import AfterSalesCase, RefundRecord


class AfterSalesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_case(self, case_id: int) -> Optional[AfterSalesCase]:
        return self.session.get(AfterSalesCase, case_id)

    def add_case(self, case: AfterSalesCase) -> AfterSalesCase:
        self.session.add(case)
        return case

    def add_refund(self, refund: RefundRecord) -> RefundRecord:
        self.session.add(refund)
        return refund

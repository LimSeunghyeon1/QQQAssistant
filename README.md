# QQQAssistant

## Use-case tests

End-to-end API happy paths are covered in `backend/tests/test_use_cases.py`:

- Product import and localization update
- Order creation with items and status transition history
- Shipment creation that links to orders and lists shipments

Run them locally:

```bash
cd backend
pip install -e .
pytest
```

## Work log

- `pip install -e backend` 실패: 외부 네트워크 프록시로 인해 `setuptools` 다운로드가 차단되어 백엔드 의존성 설치가 완료되지 않음.
- `pytest backend/tests` 실패: 위 의존성 설치 실패로 FastAPI 등을 찾지 못해 테스트 실행 불가.

## TODO

- 오프라인/사설 미러 등 네트워크 제약을 우회하거나 필요한 패키지를 수동으로 다운로드해 `pip install -e backend`가 성공하도록 처리.
- 의존성 설치가 완료된 환경에서 `pytest backend/tests`를 재실행해 유스케이스 테스트가 실제로 통과하는지 검증.

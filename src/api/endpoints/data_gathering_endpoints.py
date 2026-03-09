from src.api.api_routes import register
from src.service.zangia import ZangiaService
from src.service.lambda_global import get_all_data_and_save
from src.dependencies import get_zangia_sqlalchemy_repository, get_lambda_sqlalchemy_repository

@register(
        name="zangia/gather-data", 
        method="POST", 
        required_keys=[], 
        optional_keys={}
        )
async def gather_zangia_data(request: dict):
    repository = get_zangia_sqlalchemy_repository()
    result = ZangiaService(repository).gather_and_save()
    return result


@register(
        name="lambda/gather-data", 
        method="POST",
        required_keys=[],
        optional_keys={}
        )
async def gather_lambda_data(request: dict):
        repository = get_lambda_sqlalchemy_repository()
        result = await get_all_data_and_save(repository)
        return result
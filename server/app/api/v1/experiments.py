"""实验管理 API"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.experiment_service import (
    CustomerService, AppService, TemplateService,
    ExperimentService, ExperimentGroupService, ObjectiveMetricsService
)
from app.schemas.experiment import (
    # Customer
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerWithAppsResponse,
    # App
    AppCreate, AppUpdate, AppResponse, AppWithTemplatesResponse,
    # Template
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateWithExperimentsResponse,
    # Experiment
    ExperimentCreate, ExperimentUpdate, ExperimentResponse,
    ExperimentWithGroupsResponse, ExperimentWithDetailsResponse, ExperimentListResponse,
    # ExperimentGroup
    ExperimentGroupCreate, ExperimentGroupBatchCreate, ExperimentGroupUpdate,
    ExperimentGroupResponse, ExperimentGroupWithMetricsResponse,
    # ObjectiveMetrics
    ObjectiveMetricsCreate, ObjectiveMetricsUpdate, ObjectiveMetricsResponse,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/experiments", tags=["实验管理"])


# ============ Customer API ============

@router.get("/customers", response_model=list[CustomerResponse])
async def list_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户列表"""
    service = CustomerService(db)
    customers = await service.list_all()
    return [CustomerResponse.model_validate(c) for c in customers]


@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建客户"""
    service = CustomerService(db)
    customer = await service.create(
        name=data.name,
        contact=data.contact,
        description=data.description
    )
    return CustomerResponse.model_validate(customer)


@router.get("/customers/{customer_id}", response_model=CustomerWithAppsResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户详情"""
    service = CustomerService(db)
    customer = await service.get_by_id(customer_id)
    if not customer:
        raise NotFoundException("客户不存在")
    return CustomerWithAppsResponse.model_validate(customer)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新客户"""
    service = CustomerService(db)
    customer = await service.update(
        customer_id,
        name=data.name,
        contact=data.contact,
        description=data.description
    )
    return CustomerResponse.model_validate(customer)


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除客户"""
    service = CustomerService(db)
    await service.delete(customer_id)
    return {"message": "删除成功"}


# ============ App API ============

@router.get("/apps", response_model=list[AppResponse])
async def list_apps(
    customer_id: int = Query(None, description="客户ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用列表"""
    service = AppService(db)
    if customer_id:
        apps = await service.list_by_customer(customer_id)
    else:
        # TODO: 实现全量列表
        apps = []
    return [AppResponse.model_validate(a) for a in apps]


@router.post("/apps", response_model=AppResponse)
async def create_app(
    data: AppCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建应用"""
    service = AppService(db)
    app = await service.create(
        customer_id=data.customer_id,
        name=data.name,
        description=data.description
    )
    return AppResponse.model_validate(app)


@router.get("/apps/{app_id}", response_model=AppWithTemplatesResponse)
async def get_app(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用详情"""
    service = AppService(db)
    app = await service.get_by_id(app_id)
    if not app:
        raise NotFoundException("应用不存在")
    return AppWithTemplatesResponse.model_validate(app)


@router.put("/apps/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: int,
    data: AppUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新应用"""
    service = AppService(db)
    app = await service.update(
        app_id,
        name=data.name,
        description=data.description
    )
    return AppResponse.model_validate(app)


@router.delete("/apps/{app_id}")
async def delete_app(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除应用"""
    service = AppService(db)
    await service.delete(app_id)
    return {"message": "删除成功"}


# ============ Template API ============

@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    app_id: int = Query(None, description="应用ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板列表"""
    service = TemplateService(db)
    if app_id:
        templates = await service.list_by_app(app_id)
    else:
        templates = []
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建模板"""
    service = TemplateService(db)
    template = await service.create(
        app_id=data.app_id,
        name=data.name,
        description=data.description
    )
    return TemplateResponse.model_validate(template)


@router.get("/templates/{template_id}", response_model=TemplateWithExperimentsResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    service = TemplateService(db)
    template = await service.get_by_id(template_id)
    if not template:
        raise NotFoundException("模板不存在")
    return TemplateWithExperimentsResponse.model_validate(template)


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模板"""
    service = TemplateService(db)
    template = await service.update(
        template_id,
        name=data.name,
        description=data.description
    )
    return TemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模板"""
    service = TemplateService(db)
    await service.delete(template_id)
    return {"message": "删除成功"}


# ============ Experiment API ============

@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    template_id: int = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实验列表"""
    service = ExperimentService(db)
    experiments, total = await service.list_experiments(
        page=page,
        page_size=page_size,
        template_id=template_id,
        status=status
    )
    return ExperimentListResponse(
        items=[ExperimentResponse.model_validate(e) for e in experiments],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=ExperimentResponse)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建实验"""
    service = ExperimentService(db)
    experiment = await service.create(
        template_id=data.template_id,
        name=data.name,
        created_by=current_user.id,
        reference_type=data.reference_type.value
    )
    return ExperimentResponse.model_validate(experiment)


@router.get("/{experiment_id}", response_model=ExperimentWithDetailsResponse)
async def get_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实验详情"""
    service = ExperimentService(db)
    experiment = await service.get_by_id_with_details(experiment_id)
    if not experiment:
        raise NotFoundException("实验不存在")
    return ExperimentWithDetailsResponse.model_validate(experiment)


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: int,
    data: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新实验"""
    service = ExperimentService(db)
    update_data = data.model_dump(exclude_unset=True)
    experiment = await service.update(experiment_id, **update_data)
    return ExperimentResponse.model_validate(experiment)


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除实验"""
    service = ExperimentService(db)
    await service.delete(experiment_id)
    return {"message": "删除成功"}


# ============ ExperimentGroup API ============

@router.get("/{experiment_id}/groups", response_model=list[ExperimentGroupResponse])
async def list_experiment_groups(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实验组列表"""
    service = ExperimentGroupService(db)
    groups = await service.list_by_experiment(experiment_id)
    return [ExperimentGroupResponse.model_validate(g) for g in groups]


@router.post("/{experiment_id}/groups", response_model=ExperimentGroupResponse)
async def create_experiment_group(
    experiment_id: int,
    data: ExperimentGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建实验组"""
    service = ExperimentGroupService(db)
    group = await service.create(
        experiment_id=experiment_id,
        name=data.name,
        encoder_version=data.encoder_version,
        transcode_params=data.transcode_params,
        input_url=data.input_url,
        output_url=data.output_url,
        order_index=data.order_index
    )
    return ExperimentGroupResponse.model_validate(group)


@router.post("/{experiment_id}/groups/batch", response_model=list[ExperimentGroupResponse])
async def batch_create_experiment_groups(
    experiment_id: int,
    data: ExperimentGroupBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建实验组"""
    service = ExperimentGroupService(db)
    groups_data = [g.model_dump() for g in data.groups]
    groups = await service.batch_create(experiment_id, groups_data)
    return [ExperimentGroupResponse.model_validate(g) for g in groups]


@router.put("/groups/{group_id}", response_model=ExperimentGroupResponse)
async def update_experiment_group(
    group_id: int,
    data: ExperimentGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新实验组"""
    service = ExperimentGroupService(db)
    update_data = data.model_dump(exclude_unset=True)
    group = await service.update(group_id, **update_data)
    return ExperimentGroupResponse.model_validate(group)


@router.delete("/groups/{group_id}")
async def delete_experiment_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除实验组"""
    service = ExperimentGroupService(db)
    await service.delete(group_id)
    return {"message": "删除成功"}


# ============ ObjectiveMetrics API ============

@router.get("/groups/{group_id}/metrics", response_model=ObjectiveMetricsResponse)
async def get_objective_metrics(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实验组客观指标"""
    service = ObjectiveMetricsService(db)
    metrics = await service.get_by_group_id(group_id)
    if not metrics:
        raise NotFoundException("客观指标不存在")
    return ObjectiveMetricsResponse.model_validate(metrics)


@router.post("/groups/{group_id}/metrics", response_model=ObjectiveMetricsResponse)
async def create_or_update_objective_metrics(
    group_id: int,
    data: ObjectiveMetricsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建或更新客观指标"""
    service = ObjectiveMetricsService(db)
    metrics = await service.create_or_update(
        group_id=group_id,
        bitrate=data.bitrate,
        vmaf=data.vmaf,
        psnr=data.psnr,
        ssim=data.ssim,
        machine_type=data.machine_type,
        concurrent_streams=data.concurrent_streams,
        cpu_usage=data.cpu_usage,
        gpu_usage=data.gpu_usage,
        detailed_report_url=data.detailed_report_url
    )
    return ObjectiveMetricsResponse.model_validate(metrics)


@router.put("/groups/{group_id}/metrics", response_model=ObjectiveMetricsResponse)
async def update_objective_metrics(
    group_id: int,
    data: ObjectiveMetricsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新客观指标"""
    service = ObjectiveMetricsService(db)
    update_data = data.model_dump(exclude_unset=True)
    metrics = await service.create_or_update(group_id, **update_data)
    return ObjectiveMetricsResponse.model_validate(metrics)

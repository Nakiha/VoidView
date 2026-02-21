"""实验管理 API - Excel 存储版本"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime

from app.api.deps import get_current_user
from app.services.experiment_service import (
    CustomerService, AppService, TemplateService,
    ExperimentService, ExperimentGroupService, ObjectiveMetricsService
)
from app.schemas.experiment import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    AppCreate, AppUpdate, AppResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    ExperimentCreate, ExperimentUpdate, ExperimentResponse,
    ExperimentBrief, ExperimentListResponse,
    ExperimentTemplateLink,
    MatrixRow, MatrixResponse,
    ExperimentGroupCreate, ExperimentGroupResponse,
    ObjectiveMetricsCreate, ObjectiveMetricsResponse,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/experiments", tags=["实验管理"])


def _convert_datetime(data: dict) -> dict:
    """转换 datetime 字段为字符串"""
    result = dict(data)
    for key in ['created_at', 'updated_at', 'last_login_at']:
        if key in result and result[key] is not None:
            if isinstance(result[key], str):
                result[key] = datetime.fromisoformat(result[key])
    return result


# ============ Customer API ============

@router.get("/customers", response_model=list[CustomerResponse])
async def list_customers(
    current_user: dict = Depends(get_current_user)
):
    """获取客户列表"""
    service = CustomerService()
    customers = await service.list_all()
    return [CustomerResponse.model_validate(_convert_datetime(c)) for c in customers]


@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建客户"""
    service = CustomerService()
    customer = await service.create(
        name=data.name,
        contact=data.contact,
        description=data.description
    )
    return CustomerResponse.model_validate(_convert_datetime(customer))


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取客户详情"""
    service = CustomerService()
    customer = await service.get_by_id(customer_id)
    if not customer:
        raise NotFoundException("客户不存在")
    return CustomerResponse.model_validate(_convert_datetime(customer))


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新客户"""
    service = CustomerService()
    customer = await service.update(
        customer_id,
        name=data.name,
        contact=data.contact,
        description=data.description
    )
    return CustomerResponse.model_validate(_convert_datetime(customer))


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除客户"""
    service = CustomerService()
    await service.delete(customer_id)
    return {"message": "删除成功"}


# ============ App API ============

@router.get("/apps", response_model=list[AppResponse])
async def list_apps(
    customer_id: int = Query(None, description="客户ID"),
    current_user: dict = Depends(get_current_user)
):
    """获取应用列表"""
    service = AppService()
    if customer_id:
        apps = await service.list_by_customer(customer_id)
    else:
        apps = []
    return [AppResponse.model_validate(_convert_datetime(a)) for a in apps]


@router.post("/apps", response_model=AppResponse)
async def create_app(
    data: AppCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建应用"""
    service = AppService()
    app = await service.create(
        customer_id=data.customer_id,
        name=data.name,
        description=data.description
    )
    return AppResponse.model_validate(_convert_datetime(app))


@router.get("/apps/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取应用详情"""
    service = AppService()
    app = await service.get_by_id(app_id)
    if not app:
        raise NotFoundException("应用不存在")
    return AppResponse.model_validate(_convert_datetime(app))


@router.put("/apps/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: int,
    data: AppUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新应用"""
    service = AppService()
    app = await service.update(
        app_id,
        name=data.name,
        description=data.description
    )
    return AppResponse.model_validate(_convert_datetime(app))


@router.delete("/apps/{app_id}")
async def delete_app(
    app_id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除应用"""
    service = AppService()
    await service.delete(app_id)
    return {"message": "删除成功"}


# ============ Template API ============

@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    app_id: int = Query(None, description="应用ID"),
    current_user: dict = Depends(get_current_user)
):
    """获取模板列表"""
    service = TemplateService()
    if app_id:
        templates = await service.list_by_app(app_id)
    else:
        templates = []
    return [TemplateResponse.model_validate(_convert_datetime(t)) for t in templates]


@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建模板"""
    service = TemplateService()
    template = await service.create(
        app_id=data.app_id,
        name=data.name,
        description=data.description
    )
    return TemplateResponse.model_validate(_convert_datetime(template))


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取模板详情"""
    service = TemplateService()
    template = await service.get_by_id(template_id)
    if not template:
        raise NotFoundException("模板不存在")
    return TemplateResponse.model_validate(_convert_datetime(template))


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新模板"""
    service = TemplateService()
    template = await service.update(
        template_id,
        name=data.name,
        description=data.description
    )
    return TemplateResponse.model_validate(_convert_datetime(template))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除模板"""
    service = TemplateService()
    await service.delete(template_id)
    return {"message": "删除成功"}


# ============ Experiment API ============

@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    template_id: int = Query(None),
    status: str = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """获取实验列表"""
    from app.storage.excel_store import excel_store

    service = ExperimentService()
    experiments, total = await service.list_experiments(
        page=page,
        page_size=page_size,
        template_id=template_id,
        status=status
    )

    # 构建模板完整路径索引：template_id -> "客户/APP/模板"
    all_templates = {t["id"]: t for t in excel_store.list_templates()}
    all_apps = {a["id"]: a for a in excel_store.list_apps()}
    all_customers = {c["id"]: c for c in excel_store.list_customers()}

    template_paths = {}
    for tid, t in all_templates.items():
        app = all_apps.get(t.get("app_id"))
        if app:
            customer = all_customers.get(app.get("customer_id"))
            if customer:
                template_paths[tid] = f"{customer['name']}/{app['name']}/{t['name']}"
            else:
                template_paths[tid] = f"未知客户/{app['name']}/{t['name']}"
        else:
            template_paths[tid] = f"未知/{t['name']}"

    # 为每个实验添加模板完整路径
    items = []
    for exp in experiments:
        exp_data = _convert_datetime(exp)
        template_ids = excel_store.get_experiment_template_ids(exp["id"])
        exp_data["template_names"] = [template_paths.get(tid, f"未知模板({tid})") for tid in template_ids]
        items.append(ExperimentResponse.model_validate(exp_data))

    return ExperimentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/matrix", response_model=MatrixResponse)
async def get_experiment_matrix(
    current_user: dict = Depends(get_current_user)
):
    """获取客户矩阵数据"""
    service = ExperimentService()
    rows, experiments = await service.get_matrix_data()

    # 构建响应
    from typing import Dict as TypingDict
    matrix_rows = []
    for row in rows:
        exp_dict: TypingDict[int, ExperimentBrief] = {}
        for k, v in row["experiments"].items():
            exp_dict[int(k)] = ExperimentBrief(**v)

        matrix_rows.append(MatrixRow(
            customer_id=row["customer_id"],
            customer_name=row["customer_name"],
            app_id=row["app_id"],
            app_name=row["app_name"],
            template_id=row["template_id"],
            template_name=row["template_name"],
            experiments=exp_dict
        ))

    experiment_briefs = [
        ExperimentBrief(
            id=e["id"],
            name=e["name"],
            status=e["status"],
            color=e.get("color")
        ) for e in experiments
    ]

    return MatrixResponse(rows=matrix_rows, experiments=experiment_briefs)


@router.post("", response_model=ExperimentResponse)
async def create_experiment(
    data: ExperimentCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建实验"""
    service = ExperimentService()
    experiment = await service.create(
        template_ids=data.template_ids,
        name=data.name,
        created_by=current_user["id"],
        reference_type=data.reference_type.value
    )
    return ExperimentResponse.model_validate(_convert_datetime(experiment))


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取实验详情"""
    from app.storage.excel_store import excel_store

    service = ExperimentService()
    experiment = await service.get_by_id(experiment_id)
    if not experiment:
        raise NotFoundException("实验不存在")

    # 构建模板完整路径
    all_templates = {t["id"]: t for t in excel_store.list_templates()}
    all_apps = {a["id"]: a for a in excel_store.list_apps()}
    all_customers = {c["id"]: c for c in excel_store.list_customers()}

    template_paths = {}
    for tid, t in all_templates.items():
        app = all_apps.get(t.get("app_id"))
        if app:
            customer = all_customers.get(app.get("customer_id"))
            if customer:
                template_paths[tid] = f"{customer['name']}/{app['name']}/{t['name']}"
            else:
                template_paths[tid] = f"未知客户/{app['name']}/{t['name']}"
        else:
            template_paths[tid] = f"未知/{t['name']}"

    exp_data = _convert_datetime(experiment)
    template_ids = excel_store.get_experiment_template_ids(experiment_id)
    exp_data["template_names"] = [template_paths.get(tid, f"未知模板({tid})") for tid in template_ids]

    return ExperimentResponse.model_validate(exp_data)


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: int,
    data: ExperimentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新实验"""
    service = ExperimentService()
    update_data = data.model_dump(exclude_unset=True)
    experiment = await service.update(experiment_id, **update_data)
    return ExperimentResponse.model_validate(_convert_datetime(experiment))


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除实验"""
    service = ExperimentService()
    await service.delete(experiment_id)
    return {"message": "删除成功"}


@router.post("/{experiment_id}/templates", response_model=ExperimentResponse)
async def link_templates(
    experiment_id: int,
    data: ExperimentTemplateLink,
    current_user: dict = Depends(get_current_user)
):
    """关联模板到实验"""
    service = ExperimentService()
    experiment = await service.link_templates(experiment_id, data.template_ids)
    return ExperimentResponse.model_validate(_convert_datetime(experiment))


@router.delete("/{experiment_id}/templates/{template_id}", response_model=ExperimentResponse)
async def unlink_template(
    experiment_id: int,
    template_id: int,
    current_user: dict = Depends(get_current_user)
):
    """解除实验与模板的关联"""
    service = ExperimentService()
    experiment = await service.unlink_template(experiment_id, template_id)
    return ExperimentResponse.model_validate(_convert_datetime(experiment))


# ============ ExperimentGroup API ============

@router.get("/{experiment_id}/groups", response_model=list[ExperimentGroupResponse])
async def list_experiment_groups(
    experiment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取实验组列表"""
    service = ExperimentGroupService()
    groups = await service.list_by_experiment(experiment_id)
    return [ExperimentGroupResponse.model_validate(g) for g in groups]


@router.post("/{experiment_id}/groups", response_model=ExperimentGroupResponse)
async def create_experiment_group(
    experiment_id: int,
    data: ExperimentGroupCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建实验组"""
    service = ExperimentGroupService()
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


# ============ ObjectiveMetrics API ============

@router.get("/groups/{group_id}/metrics", response_model=ObjectiveMetricsResponse)
async def get_objective_metrics(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取实验组客观指标"""
    service = ObjectiveMetricsService()
    metrics = await service.get_by_group_id(group_id)
    if not metrics:
        raise NotFoundException("客观指标不存在")
    return ObjectiveMetricsResponse.model_validate(metrics)


@router.post("/groups/{group_id}/metrics", response_model=ObjectiveMetricsResponse)
async def create_or_update_objective_metrics(
    group_id: int,
    data: ObjectiveMetricsCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建或更新客观指标"""
    service = ObjectiveMetricsService()
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

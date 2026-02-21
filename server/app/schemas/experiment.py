"""实验相关的 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, Field

from voidview_shared import ExperimentStatus, GroupStatus, ReferenceType


# ============ Customer ============

class CustomerBase(BaseModel):
    """客户基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    contact: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class CustomerCreate(CustomerBase):
    """创建客户请求"""
    pass


class CustomerUpdate(BaseModel):
    """更新客户请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class CustomerResponse(CustomerBase):
    """客户响应"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerWithAppsResponse(CustomerResponse):
    """客户响应（含应用列表）"""
    apps: List["AppResponse"] = []


# ============ App ============

class AppBase(BaseModel):
    """应用基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class AppCreate(AppBase):
    """创建应用请求"""
    customer_id: int


class AppUpdate(BaseModel):
    """更新应用请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class AppResponse(AppBase):
    """应用响应"""
    id: int
    customer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AppWithTemplatesResponse(AppResponse):
    """应用响应（含模板列表）"""
    templates: List["TemplateResponse"] = []


# ============ Template ============

class TemplateBase(BaseModel):
    """模板基础模型"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class TemplateCreate(TemplateBase):
    """创建模板请求"""
    app_id: int


class TemplateUpdate(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None


class TemplateResponse(TemplateBase):
    """模板响应"""
    id: int
    app_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateBrief(TemplateBase):
    """模板简要响应（用于嵌套）"""
    id: int
    app_id: int

    class Config:
        from_attributes = True


class TemplateWithExperimentsResponse(TemplateResponse):
    """模板响应（含实验列表）"""
    experiments: List["ExperimentResponse"] = []


class TemplateWithParentResponse(TemplateResponse):
    """模板响应（含父级信息）"""
    app_name: str
    customer_id: int
    customer_name: str


# ============ Experiment ============

class ExperimentBase(BaseModel):
    """实验基础模型"""
    name: str = Field(..., min_length=1, max_length=200)
    reference_type: ReferenceType = ReferenceType.NEW


class ExperimentCreate(ExperimentBase):
    """创建实验请求"""
    template_ids: List[int] = Field(..., min_length=1, description="关联的模板ID列表")


class ExperimentUpdate(BaseModel):
    """更新实验请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[ExperimentStatus] = None
    reference_type: Optional[ReferenceType] = None
    color: Optional[str] = Field(None, max_length=10)


class ExperimentResponse(ExperimentBase):
    """实验响应"""
    id: int
    status: ExperimentStatus
    color: Optional[str] = None
    template_names: List[str] = []  # 关联的模板名称列表
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExperimentBrief(BaseModel):
    """实验简要信息（用于矩阵和卡片）"""
    id: int
    name: str
    status: ExperimentStatus
    color: Optional[str] = None

    class Config:
        from_attributes = True


class ExperimentWithTemplatesResponse(ExperimentResponse):
    """实验响应（含关联模板列表）"""
    templates: List["TemplateBrief"] = []


class ExperimentWithGroupsResponse(ExperimentResponse):
    """实验响应（含实验组列表）"""
    templates: List["TemplateBrief"] = []
    groups: List["ExperimentGroupResponse"] = []


class ExperimentWithDetailsResponse(ExperimentResponse):
    """实验响应（含完整详情）"""
    templates: List["TemplateWithParentResponse"] = []
    creator: "UserBriefResponse"
    groups: List["ExperimentGroupResponse"] = []


class UserBriefResponse(BaseModel):
    """用户简要响应"""
    id: int
    username: str
    display_name: str

    class Config:
        from_attributes = True


# ============ 矩阵相关 ============

class MatrixRow(BaseModel):
    """矩阵行数据"""
    customer_id: int
    customer_name: str
    app_id: int
    app_name: str
    template_id: int
    template_name: str
    experiments: Dict[int, ExperimentBrief] = Field(default_factory=dict, description="{experiment_id: ExperimentBrief}")


class MatrixResponse(BaseModel):
    """矩阵响应"""
    rows: List[MatrixRow]
    experiments: List[ExperimentBrief]  # 所有实验（作为列头）


class ExperimentTemplateLink(BaseModel):
    """实验-模板关联请求"""
    template_ids: List[int]


# ============ ExperimentGroup ============

class ExperimentGroupBase(BaseModel):
    """实验组基础模型"""
    name: str = Field(..., min_length=1, max_length=200)
    encoder_version: Optional[str] = Field(None, max_length=100)
    transcode_params: Optional[dict] = None
    input_url: Optional[str] = None
    output_url: Optional[str] = None


class ExperimentGroupCreate(ExperimentGroupBase):
    """创建实验组请求"""
    experiment_id: int
    order_index: int = 0


class ExperimentGroupBatchCreate(BaseModel):
    """批量创建实验组请求"""
    experiment_id: int
    groups: List[ExperimentGroupBase]


class ExperimentGroupUpdate(BaseModel):
    """更新实验组请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    encoder_version: Optional[str] = Field(None, max_length=100)
    transcode_params: Optional[dict] = None
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    status: Optional[GroupStatus] = None
    order_index: Optional[int] = None


class ExperimentGroupResponse(ExperimentGroupBase):
    """实验组响应"""
    id: int
    experiment_id: int
    status: GroupStatus
    order_index: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExperimentGroupWithMetricsResponse(ExperimentGroupResponse):
    """实验组响应（含客观指标）"""
    objective_metrics: Optional["ObjectiveMetricsResponse"] = None


# ============ ObjectiveMetrics ============

class ObjectiveMetricsBase(BaseModel):
    """客观指标基础模型"""
    bitrate: Optional[float] = Field(None, ge=0)
    vmaf: Optional[float] = Field(None, ge=0, le=100)
    psnr: Optional[float] = Field(None, ge=0)
    ssim: Optional[float] = Field(None, ge=0, le=1)
    machine_type: Optional[str] = Field(None, max_length=100)
    concurrent_streams: int = Field(0, ge=0)
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    gpu_usage: Optional[float] = Field(None, ge=0, le=100)
    detailed_report_url: Optional[str] = None


class ObjectiveMetricsCreate(ObjectiveMetricsBase):
    """创建客观指标请求"""
    group_id: int


class ObjectiveMetricsUpdate(BaseModel):
    """更新客观指标请求"""
    bitrate: Optional[float] = Field(None, ge=0)
    vmaf: Optional[float] = Field(None, ge=0, le=100)
    psnr: Optional[float] = Field(None, ge=0)
    ssim: Optional[float] = Field(None, ge=0, le=1)
    machine_type: Optional[str] = Field(None, max_length=100)
    concurrent_streams: Optional[int] = Field(None, ge=0)
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    gpu_usage: Optional[float] = Field(None, ge=0, le=100)
    detailed_report_url: Optional[str] = None


class ObjectiveMetricsResponse(ObjectiveMetricsBase):
    """客观指标响应"""
    id: int
    group_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ List Response ============

class ExperimentListResponse(BaseModel):
    """实验列表响应"""
    items: List[ExperimentResponse]
    total: int
    page: int
    page_size: int


class PaginatedResponse(BaseModel):
    """通用分页响应"""
    total: int
    page: int
    page_size: int


# 更新 forward references
CustomerWithAppsResponse.model_rebuild()
AppWithTemplatesResponse.model_rebuild()
TemplateWithExperimentsResponse.model_rebuild()
ExperimentWithTemplatesResponse.model_rebuild()
ExperimentWithGroupsResponse.model_rebuild()
ExperimentWithDetailsResponse.model_rebuild()
ExperimentGroupWithMetricsResponse.model_rebuild()

"""实验相关模型"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from voidview_shared import ExperimentStatus, GroupStatus, ReferenceType


# ============ Customer ============

class CustomerResponse(BaseModel):
    """客户响应模型"""
    id: int
    name: str
    contact: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerCreateRequest(BaseModel):
    """创建客户请求"""
    name: str = Field(..., min_length=1, max_length=100)
    contact: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class CustomerUpdateRequest(BaseModel):
    """更新客户请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


# ============ App ============

class AppResponse(BaseModel):
    """应用响应模型"""
    id: int
    customer_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AppCreateRequest(BaseModel):
    """创建应用请求"""
    customer_id: int
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class AppUpdateRequest(BaseModel):
    """更新应用请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


# ============ Template ============

class TemplateResponse(BaseModel):
    """模板响应模型"""
    id: int
    app_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateCreateRequest(BaseModel):
    """创建模板请求"""
    app_id: int
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class TemplateUpdateRequest(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None


# ============ Experiment ============

class ExperimentResponse(BaseModel):
    """实验响应模型"""
    id: int
    template_id: int
    name: str
    status: ExperimentStatus
    reference_type: ReferenceType
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExperimentCreateRequest(BaseModel):
    """创建实验请求"""
    template_id: int
    name: str = Field(..., min_length=1, max_length=200)
    reference_type: ReferenceType = ReferenceType.NEW


class ExperimentUpdateRequest(BaseModel):
    """更新实验请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[ExperimentStatus] = None
    reference_type: Optional[ReferenceType] = None


class ExperimentListResponse(BaseModel):
    """实验列表响应"""
    items: List[ExperimentResponse]
    total: int
    page: int
    page_size: int


# ============ ExperimentGroup ============

class ExperimentGroupResponse(BaseModel):
    """实验组响应模型"""
    id: int
    experiment_id: int
    name: str
    encoder_version: Optional[str] = None
    transcode_params: Optional[dict] = None
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    status: GroupStatus
    order_index: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExperimentGroupCreateRequest(BaseModel):
    """创建实验组请求"""
    experiment_id: int
    name: str = Field(..., min_length=1, max_length=200)
    encoder_version: Optional[str] = Field(None, max_length=100)
    transcode_params: Optional[dict] = None
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    order_index: int = 0


class ExperimentGroupBatchCreateRequest(BaseModel):
    """批量创建实验组请求"""
    experiment_id: int
    groups: List[dict]


class ExperimentGroupUpdateRequest(BaseModel):
    """更新实验组请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    encoder_version: Optional[str] = Field(None, max_length=100)
    transcode_params: Optional[dict] = None
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    status: Optional[GroupStatus] = None
    order_index: Optional[int] = None


# ============ ObjectiveMetrics ============

class ObjectiveMetricsResponse(BaseModel):
    """客观指标响应模型"""
    id: int
    group_id: int
    bitrate: Optional[float] = None
    vmaf: Optional[float] = None
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    machine_type: Optional[str] = None
    concurrent_streams: int = 0
    cpu_usage: Optional[float] = None
    gpu_usage: Optional[float] = None
    detailed_report_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ObjectiveMetricsCreateRequest(BaseModel):
    """创建客观指标请求"""
    group_id: int
    bitrate: Optional[float] = Field(None, ge=0)
    vmaf: Optional[float] = Field(None, ge=0, le=100)
    psnr: Optional[float] = Field(None, ge=0)
    ssim: Optional[float] = Field(None, ge=0, le=1)
    machine_type: Optional[str] = Field(None, max_length=100)
    concurrent_streams: int = Field(0, ge=0)
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    gpu_usage: Optional[float] = Field(None, ge=0, le=100)
    detailed_report_url: Optional[str] = None


class ObjectiveMetricsUpdateRequest(BaseModel):
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

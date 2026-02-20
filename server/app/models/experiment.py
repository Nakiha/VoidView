"""实验相关模型"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean, Enum as SQLEnum, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from voidview_shared import ExperimentStatus, GroupStatus, ReferenceType


class Customer(Base):
    """客户"""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="客户名称")
    contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="联系人")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联
    apps: Mapped[List["App"]] = relationship("App", back_populates="customer", cascade="all, delete-orphan")


class App(Base):
    """应用"""
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="应用名")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联
    customer: Mapped["Customer"] = relationship("Customer", back_populates="apps")
    templates: Mapped[List["Template"]] = relationship("Template", back_populates="app", cascade="all, delete-orphan")


class Template(Base):
    """转码模板"""
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    app_id: Mapped[int] = mapped_column(Integer, ForeignKey("apps.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="模板名 如 hd5, uhd")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联
    app: Mapped["App"] = relationship("App", back_populates="templates")
    experiments: Mapped[List["Experiment"]] = relationship("Experiment", back_populates="template", cascade="all, delete-orphan")


class Experiment(Base):
    """实验"""
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("templates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="实验名")
    status: Mapped[ExperimentStatus] = mapped_column(
        SQLEnum(ExperimentStatus),
        default=ExperimentStatus.DRAFT,
        nullable=False
    )
    reference_type: Mapped[ReferenceType] = mapped_column(
        SQLEnum(ReferenceType),
        default=ReferenceType.NEW,
        nullable=False,
        comment="参考类型: supplier/self/new"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关联
    template: Mapped["Template"] = relationship("Template", back_populates="experiments")
    creator: Mapped["User"] = relationship("User")
    groups: Mapped[List["ExperimentGroup"]] = relationship("ExperimentGroup", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentGroup(Base):
    """实验组"""
    __tablename__ = "experiment_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(Integer, ForeignKey("experiments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="实验组名 如 hd5_0215_roi01")
    encoder_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="转码服务镜像版本")
    transcode_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="转码参数 JSON")
    input_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="入流链接")
    output_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="出流链接")
    status: Mapped[GroupStatus] = mapped_column(
        SQLEnum(GroupStatus),
        default=GroupStatus.PENDING,
        nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序序号")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关联
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="groups")
    objective_metrics: Mapped[Optional["ObjectiveMetrics"]] = relationship(
        "ObjectiveMetrics", back_populates="group", uselist=False, cascade="all, delete-orphan"
    )


class ObjectiveMetrics(Base):
    """客观指标"""
    __tablename__ = "objective_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("experiment_groups.id"), nullable=False, unique=True)

    # 码率和质量指标
    bitrate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="比特率 kbps")
    vmaf: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="VMAF 分值")
    psnr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="PSNR 分值")
    ssim: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="SSIM 分值")

    # 性能指标
    machine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="机型")
    concurrent_streams: Mapped[int] = mapped_column(Integer, default=0, comment="并发路数")
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="CPU 使用率")
    gpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="GPU 使用率")

    # 详细报告
    detailed_report_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整指标sheet链接")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关联
    group: Mapped["ExperimentGroup"] = relationship("ExperimentGroup", back_populates="objective_metrics")


# 延迟导入避免循环引用
from app.models.user import User

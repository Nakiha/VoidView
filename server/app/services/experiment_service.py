"""实验服务"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.experiment import Customer, App, Template, Experiment, ExperimentGroup, ObjectiveMetrics
from app.core.exceptions import BadRequestException, NotFoundException
from voidview_shared import ExperimentStatus, GroupStatus


class CustomerService:
    """客户服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """根据ID获取客户"""
        return await self.db.get(Customer, customer_id)

    async def get_by_name(self, name: str) -> Optional[Customer]:
        """根据名称获取客户"""
        stmt = select(Customer).where(Customer.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, name: str, contact: str = None, description: str = None) -> Customer:
        """创建客户"""
        existing = await self.get_by_name(name)
        if existing:
            raise BadRequestException("客户名称已存在")

        customer = Customer(name=name, contact=contact, description=description)
        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def update(self, customer_id: int, **kwargs) -> Customer:
        """更新客户"""
        customer = await self.get_by_id(customer_id)
        if not customer:
            raise NotFoundException("客户不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(customer, key):
                setattr(customer, key, value)

        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def delete(self, customer_id: int) -> None:
        """删除客户"""
        customer = await self.get_by_id(customer_id)
        if not customer:
            raise NotFoundException("客户不存在")

        await self.db.delete(customer)
        await self.db.commit()

    async def list_all(self) -> List[Customer]:
        """获取所有客户"""
        stmt = select(Customer).order_by(Customer.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class AppService:
    """应用服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, app_id: int) -> Optional[App]:
        """根据ID获取应用"""
        return await self.db.get(App, app_id)

    async def create(self, customer_id: int, name: str, description: str = None) -> App:
        """创建应用"""
        app = App(customer_id=customer_id, name=name, description=description)
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def update(self, app_id: int, **kwargs) -> App:
        """更新应用"""
        app = await self.get_by_id(app_id)
        if not app:
            raise NotFoundException("应用不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(app, key):
                setattr(app, key, value)

        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def delete(self, app_id: int) -> None:
        """删除应用"""
        app = await self.get_by_id(app_id)
        if not app:
            raise NotFoundException("应用不存在")

        await self.db.delete(app)
        await self.db.commit()

    async def list_by_customer(self, customer_id: int) -> List[App]:
        """获取客户下的所有应用"""
        stmt = select(App).where(App.customer_id == customer_id).order_by(App.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class TemplateService:
    """模板服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, template_id: int) -> Optional[Template]:
        """根据ID获取模板"""
        return await self.db.get(Template, template_id)

    async def create(self, app_id: int, name: str, description: str = None) -> Template:
        """创建模板"""
        template = Template(app_id=app_id, name=name, description=description)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update(self, template_id: int, **kwargs) -> Template:
        """更新模板"""
        template = await self.get_by_id(template_id)
        if not template:
            raise NotFoundException("模板不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template_id: int) -> None:
        """删除模板"""
        template = await self.get_by_id(template_id)
        if not template:
            raise NotFoundException("模板不存在")

        await self.db.delete(template)
        await self.db.commit()

    async def list_by_app(self, app_id: int) -> List[Template]:
        """获取应用下的所有模板"""
        stmt = select(Template).where(Template.app_id == app_id).order_by(Template.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ExperimentService:
    """实验服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, experiment_id: int) -> Optional[Experiment]:
        """根据ID获取实验"""
        return await self.db.get(Experiment, experiment_id)

    async def get_by_id_with_details(self, experiment_id: int) -> Optional[Experiment]:
        """根据ID获取实验（含关联数据）"""
        stmt = (
            select(Experiment)
            .options(selectinload(Experiment.template), selectinload(Experiment.creator))
            .where(Experiment.id == experiment_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        template_id: int,
        name: str,
        created_by: int,
        reference_type: str = "new"
    ) -> Experiment:
        """创建实验"""
        experiment = Experiment(
            template_id=template_id,
            name=name,
            created_by=created_by,
            reference_type=reference_type,
            status=ExperimentStatus.DRAFT
        )
        self.db.add(experiment)
        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    async def update(self, experiment_id: int, **kwargs) -> Experiment:
        """更新实验"""
        experiment = await self.get_by_id(experiment_id)
        if not experiment:
            raise NotFoundException("实验不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(experiment, key):
                setattr(experiment, key, value)

        experiment.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    async def delete(self, experiment_id: int) -> None:
        """删除实验"""
        experiment = await self.get_by_id(experiment_id)
        if not experiment:
            raise NotFoundException("实验不存在")

        await self.db.delete(experiment)
        await self.db.commit()

    async def list_experiments(
        self,
        page: int = 1,
        page_size: int = 20,
        template_id: int = None,
        status: str = None
    ) -> tuple[List[Experiment], int]:
        """获取实验列表"""
        stmt = select(Experiment)

        if template_id:
            stmt = stmt.where(Experiment.template_id == template_id)
        if status:
            stmt = stmt.where(Experiment.status == status)

        # 统计总数
        count_stmt = select(func.count(Experiment.id))
        if template_id:
            count_stmt = count_stmt.where(Experiment.template_id == template_id)
        if status:
            count_stmt = count_stmt.where(Experiment.status == status)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页查询
        stmt = stmt.order_by(Experiment.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        experiments = list(result.scalars().all())

        return experiments, total


class ExperimentGroupService:
    """实验组服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, group_id: int) -> Optional[ExperimentGroup]:
        """根据ID获取实验组"""
        return await self.db.get(ExperimentGroup, group_id)

    async def create(
        self,
        experiment_id: int,
        name: str,
        encoder_version: str = None,
        transcode_params: dict = None,
        input_url: str = None,
        output_url: str = None,
        order_index: int = 0
    ) -> ExperimentGroup:
        """创建实验组"""
        group = ExperimentGroup(
            experiment_id=experiment_id,
            name=name,
            encoder_version=encoder_version,
            transcode_params=transcode_params,
            input_url=input_url,
            output_url=output_url,
            order_index=order_index,
            status=GroupStatus.PENDING
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def batch_create(self, experiment_id: int, groups_data: List[dict]) -> List[ExperimentGroup]:
        """批量创建实验组"""
        groups = []
        for i, data in enumerate(groups_data):
            group = ExperimentGroup(
                experiment_id=experiment_id,
                name=data.get("name"),
                encoder_version=data.get("encoder_version"),
                transcode_params=data.get("transcode_params"),
                input_url=data.get("input_url"),
                output_url=data.get("output_url"),
                order_index=data.get("order_index", i),
                status=GroupStatus.PENDING
            )
            groups.append(group)
            self.db.add(group)

        await self.db.commit()
        for group in groups:
            await self.db.refresh(group)
        return groups

    async def update(self, group_id: int, **kwargs) -> ExperimentGroup:
        """更新实验组"""
        group = await self.get_by_id(group_id)
        if not group:
            raise NotFoundException("实验组不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(group, key):
                setattr(group, key, value)

        group.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def delete(self, group_id: int) -> None:
        """删除实验组"""
        group = await self.get_by_id(group_id)
        if not group:
            raise NotFoundException("实验组不存在")

        await self.db.delete(group)
        await self.db.commit()

    async def list_by_experiment(self, experiment_id: int) -> List[ExperimentGroup]:
        """获取实验下的所有实验组"""
        stmt = (
            select(ExperimentGroup)
            .where(ExperimentGroup.experiment_id == experiment_id)
            .order_by(ExperimentGroup.order_index, ExperimentGroup.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ObjectiveMetricsService:
    """客观指标服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_group_id(self, group_id: int) -> Optional[ObjectiveMetrics]:
        """根据实验组ID获取客观指标"""
        stmt = select(ObjectiveMetrics).where(ObjectiveMetrics.group_id == group_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(self, group_id: int, **kwargs) -> ObjectiveMetrics:
        """创建或更新客观指标"""
        metrics = await self.get_by_group_id(group_id)

        if metrics:
            for key, value in kwargs.items():
                if value is not None and hasattr(metrics, key):
                    setattr(metrics, key, value)
            metrics.updated_at = datetime.utcnow()
        else:
            metrics = ObjectiveMetrics(group_id=group_id, **kwargs)
            self.db.add(metrics)

        await self.db.commit()
        await self.db.refresh(metrics)
        return metrics

    async def delete_by_group_id(self, group_id: int) -> None:
        """删除实验组的客观指标"""
        metrics = await self.get_by_group_id(group_id)
        if metrics:
            await self.db.delete(metrics)
            await self.db.commit()

# 数据模型与持久化指南

此 SKILL 用于指导 VoidView 项目中数据模型设计和 SQLite 持久化实现。

## 技术选型

- **ORM**: SQLAlchemy 2.0 (支持 async)
- **数据库**: SQLite (单文件，便于归档和迁移)
- **数据验证**: Pydantic v2
- **迁移工具**: Alembic
- **密码哈希**: bcrypt

## 数据库配置

```python
# src/data/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

# 数据库文件路径
DB_PATH = Path("data/database/voidview.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=False  # 生产环境关闭 SQL 日志
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


def get_db():
    """获取数据库会话 (依赖注入)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
```

## 核心数据模型

### 0. 用户与权限

```python
# src/core/models/user.py
from enum import Enum
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from data.database import Base
import bcrypt


class UserRole(str, Enum):
    ROOT = "root"        # 管理员 - 可以创建账号、管理所有数据
    TESTER = "tester"    # 测试人员 - 可以参与评测和评审


class User(Base):
    """用户账号"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))  # bcrypt hash
    display_name: Mapped[str] = mapped_column(String(100))   # 显示名称
    role: Mapped[UserRole] = mapped_column(default=UserRole.TESTER)
    is_active: Mapped[bool] = mapped_column(default=True)
    must_change_password: Mapped[bool] = mapped_column(default=False)  # 首次登录需改密

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def set_password(self, password: str):
        """设置密码 (自动哈希)"""
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def is_root(self) -> bool:
        """是否为管理员"""
        return self.role == UserRole.ROOT

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# 用户服务
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        if user and user.verify_password(password):
            user.last_login_at = datetime.utcnow()
            self.db.commit()
            return user
        return None

    def create_user(self, username: str, password: str, display_name: str,
                    created_by: int, role: UserRole = UserRole.TESTER) -> User:
        """创建用户 (仅 root 可调用)"""
        user = User(
            username=username,
            display_name=display_name,
            role=role,
            created_by=created_by,
            must_change_password=True  # 首次登录需修改密码
        )
        user.set_password(password)
        self.db.add(user)
        self.db.commit()
        return user

    def init_root_user(self):
        """初始化 root 账号"""
        if not self.db.query(User).filter(User.role == UserRole.ROOT).first():
            root = User(
                username="root",
                display_name="系统管理员",
                role=UserRole.ROOT,
                must_change_password=True
            )
            root.set_password("root123")  # 默认密码，首次登录需修改
            self.db.add(root)
            self.db.commit()
            return root
        return None
```

### 1. 客户与应用

```python
# src/core/models/customer.py
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from data.database import Base


class Customer(Base):
    """客户"""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    apps: Mapped[List["App"]] = relationship(back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.name}>"


class App(Base):
    """应用"""
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    customer: Mapped["Customer"] = relationship(back_populates="apps")
    templates: Mapped[List["Template"]] = relationship(back_populates="app", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<App {self.name}>"
```

### 2. 模板与实验

```python
# src/core/models/experiment.py
from enum import Enum
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional, Dict


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ReferenceType(str, Enum):
    SUPPLIER = "supplier"  # 对齐其他供应商
    SELF = "self"          # 自对齐(降低码率)
    NEW = "new"            # 全新模板


class GroupStatus(str, Enum):
    PENDING = "pending"
    OBJECTIVE_PASS = "objective_pass"
    OBJECTIVE_FAIL = "objective_fail"
    SUBJECTIVE_PASS = "subjective_pass"
    SUBJECTIVE_FAIL = "subjective_fail"
    ONLINE = "online"
    REJECTED = "rejected"


class Template(Base):
    """转码模板"""
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    name: Mapped[str] = mapped_column(String(50), index=True)  # hd5, uhd, ld5
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    app: Mapped["App"] = relationship(back_populates="templates")
    experiments: Mapped[List["Experiment"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class Experiment(Base):
    """实验"""
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)  # "xx客户third_app实验"
    status: Mapped[ExperimentStatus] = mapped_column(SQLEnum(ExperimentStatus), default=ExperimentStatus.DRAFT)
    reference_type: Mapped[ReferenceType] = mapped_column(SQLEnum(ReferenceType))
    reference_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # 参考视频链接
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String(100))
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # 关联
    template: Mapped["Template"] = relationship(back_populates="experiments")
    groups: Mapped[List["ExperimentGroup"]] = relationship(back_populates="experiment", cascade="all, delete-orphan")


class ExperimentGroup(Base):
    """实验组"""
    __tablename__ = "experiment_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)  # hd5_0215_roi01
    encoder_version: Mapped[str] = mapped_column(String(100))  # 镜像版本
    transcode_params: Mapped[Dict] = mapped_column(JSON)  # 转码参数 JSON
    input_url: Mapped[str] = mapped_column(String(500))  # 入流链接
    output_url: Mapped[str] = mapped_column(String(500))  # 出流链接
    status: Mapped[GroupStatus] = mapped_column(SQLEnum(GroupStatus), default=GroupStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    experiment: Mapped["Experiment"] = relationship(back_populates="groups")
    objective_metrics: Mapped[Optional["ObjectiveMetrics"]] = relationship(back_populates="group", uselist=False, cascade="all, delete-orphan")
    subjective_results: Mapped[List["SubjectiveResult"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    online_metrics: Mapped[Optional["OnlineMetrics"]] = relationship(back_populates="group", uselist=False, cascade="all, delete-orphan")
```

### 3. 评测数据

```python
# src/core/models/evaluation.py
from enum import Enum
from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional, Dict


class EvaluationType(str, Enum):
    STATIC_FRAME = "static_frame"  # 静帧评测
    BLIND_TEST = "blind_test"      # 盲测


class ObjectiveMetrics(Base):
    """客观指标"""
    __tablename__ = "objective_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("experiment_groups.id"), unique=True, index=True)

    # 码率相关
    bitrate: Mapped[float] = mapped_column(Float)  # kbps
    input_bitrate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 原始码率

    # 质量指标
    vmaf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    psnr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ssim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 性能指标
    machine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    concurrent_streams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 百分比
    gpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 百分比
    encoding_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # fps

    # 其他
    detailed_report_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)  # 原始数据

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    group: Mapped["ExperimentGroup"] = relationship(back_populates="objective_metrics")


class SubjectiveResult(Base):
    """主观评测结果"""
    __tablename__ = "subjective_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("experiment_groups.id"), index=True)
    evaluator: Mapped[str] = mapped_column(String(100))  # 评测人员
    evaluation_type: Mapped[EvaluationType] = mapped_column(default=EvaluationType.STATIC_FRAME)

    # 静帧评测
    has_artifacts: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    blur_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    artifact_types: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # ["mosaic", "ringing", ...]
    artifact_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 盲测
    blind_test_winner: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "experiment" / "reference"

    # 通用
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_doc_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    group: Mapped["ExperimentGroup"] = relationship(back_populates="subjective_results")
    screenshots: Mapped[List["Screenshot"]] = relationship(back_populates="subjective_result", cascade="all, delete-orphan")


class Screenshot(Base):
    """评测截图"""
    __tablename__ = "screenshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    subjective_result_id: Mapped[int] = mapped_column(ForeignKey("subjective_results.id"), index=True)

    file_path: Mapped[str] = mapped_column(String(500))  # 截图存储路径
    annotation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 标注描述
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # blur/mosaic/ringing/artifact
    timestamp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 视频时间戳

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    subjective_result: Mapped["SubjectiveResult"] = relationship(back_populates="screenshots")
```

### 4. 评审与上线

```python
# src/core/models/review.py
from enum import Enum
from sqlalchemy import String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional


class ReviewType(str, Enum):
    OBJECTIVE = "objective"    # 客观指标评审
    SUBJECTIVE = "subjective"  # 主观评测评审


class ReviewResult(str, Enum):
    PENDING = "pending"
    PASS = "pass"
    REJECT = "reject"


class Review(Base):
    """评审记录"""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("experiment_groups.id"), index=True)
    reviewer: Mapped[str] = mapped_column(String(100))  # 评审人
    review_type: Mapped[ReviewType] = mapped_column(default=ReviewType.SUBJECTIVE)
    result: Mapped[ReviewResult] = mapped_column(default=ReviewResult.PENDING)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关联
    group: Mapped["ExperimentGroup"] = relationship(back_populates="reviews")


class OnlineMetrics(Base):
    """上线后看播指标"""
    __tablename__ = "online_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("experiment_groups.id"), unique=True, index=True)

    # 看播指标
    ctr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 点击率
    pull_success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 拉流成功率
    penetration_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 渗透率
    avg_watch_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 平均观看时长

    # 成本指标
    bandwidth_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 带宽成本
    compute_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 计算成本

    collected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 关联
    group: Mapped["ExperimentGroup"] = relationship(back_populates="online_metrics")
```

## 数据仓库 (Repository)

```python
# src/data/repositories/experiment_repo.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from core.models.experiment import Experiment, ExperimentGroup, ExperimentStatus


class ExperimentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, experiment: Experiment) -> Experiment:
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        return experiment

    def get_by_id(self, experiment_id: int) -> Optional[Experiment]:
        return self.db.get(Experiment, experiment_id)

    def get_by_status(self, status: ExperimentStatus) -> List[Experiment]:
        stmt = select(Experiment).where(Experiment.status == status)
        return self.db.scalars(stmt).all()

    def get_with_groups(self, experiment_id: int) -> Optional[Experiment]:
        """获取实验及其所有实验组"""
        stmt = select(Experiment).where(Experiment.id == experiment_id)
        experiment = self.db.scalars(stmt).first()
        if experiment:
            # 预加载关联
            _ = experiment.groups
        return experiment

    def update_status(self, experiment_id: int, status: ExperimentStatus) -> None:
        experiment = self.get_by_id(experiment_id)
        if experiment:
            experiment.status = status
            self.db.commit()

    def add_group(self, experiment_id: int, group: ExperimentGroup) -> ExperimentGroup:
        group.experiment_id = experiment_id
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group


# 使用示例
def example_usage():
    from data.database import SessionLocal

    db = SessionLocal()
    repo = ExperimentRepository(db)

    # 创建实验
    experiment = Experiment(
        template_id=1,
        name="测试客户third_app实验",
        status=ExperimentStatus.DRAFT,
        reference_type=ReferenceType.NEW,
        created_by="张三"
    )
    repo.create(experiment)

    # 获取进行中的实验
    running_experiments = repo.get_by_status(ExperimentStatus.RUNNING)

    db.close()
```

## Pydantic 模型 (用于 API 和验证)

```python
# src/core/schemas/experiment.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class ExperimentCreate(BaseModel):
    """创建实验请求"""
    template_id: int
    name: str = Field(..., min_length=1, max_length=200)
    reference_type: str
    reference_url: Optional[str] = None


class ExperimentGroupCreate(BaseModel):
    """创建实验组请求"""
    name: str = Field(..., min_length=1, max_length=100)
    encoder_version: str
    transcode_params: Dict
    input_url: str
    output_url: str


class ObjectiveMetricsCreate(BaseModel):
    """创建客观指标请求"""
    bitrate: float
    vmaf: Optional[float] = None
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    machine_type: Optional[str] = None
    concurrent_streams: Optional[int] = None
    cpu_usage: Optional[float] = None
    gpu_usage: Optional[float] = None


class SubjectiveResultCreate(BaseModel):
    """创建主观评测结果请求"""
    evaluator: str
    evaluation_type: str = "static_frame"
    has_artifacts: Optional[bool] = None
    blur_score: Optional[int] = Field(None, ge=1, le=5)
    artifact_types: Optional[List[str]] = None
    notes: Optional[str] = None


class ExperimentResponse(BaseModel):
    """实验响应"""
    id: int
    name: str
    status: str
    reference_type: str
    created_at: datetime
    groups: List["ExperimentGroupResponse"] = []

    class Config:
        from_attributes = True


class ExperimentGroupResponse(BaseModel):
    """实验组响应"""
    id: int
    name: str
    encoder_version: str
    status: str
    objective_metrics: Optional[dict] = None

    class Config:
        from_attributes = True
```

## 数据库迁移

```bash
# 初始化迁移
alembic init src/data/migrations

# 生成迁移脚本
alembic revision --autogenerate -m "Initial tables"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 查询示例

```python
# 常用查询

# 1. 获取某客户所有实验
def get_customer_experiments(db: Session, customer_id: int):
    return db.query(Experiment).join(Template).join(App).filter(
        App.customer_id == customer_id
    ).all()

# 2. 获取待主观评测的实验组
def get_pending_subjective_groups(db: Session):
    return db.query(ExperimentGroup).filter(
        ExperimentGroup.status == GroupStatus.OBJECTIVE_PASS
    ).all()

# 3. 统计某模板的平均VMAF
from sqlalchemy import func

def get_avg_vmaf_by_template(db: Session, template_id: int):
    return db.query(func.avg(ObjectiveMetrics.vmaf)).join(ExperimentGroup).join(
        Experiment
    ).filter(
        Experiment.template_id == template_id
    ).scalar()

# 4. 获取实验组完整信息 (包含所有关联)
def get_group_full_info(db: Session, group_id: int):
    group = db.get(ExperimentGroup, group_id)
    if group:
        _ = group.objective_metrics
        _ = group.subjective_results
        _ = group.reviews
    return group
```

## 注意事项

1. 使用 `sessionmaker` 管理会话，避免连接泄漏
2. 大量数据操作使用批量插入 (`bulk_save_objects`)
3. 复杂查询考虑使用 SQLAlchemy Core
4. 定期备份数据库文件
5. 敏感字段考虑加密存储

## 登录与权限控制

### 登录界面

```python
# src/ui/login_dialog.py
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    SubtitleLabel, LineEdit, PrimaryPushButton, PushButton,
    InfoBar, FluentIcon, MessageBox
)
from core.models.user import User, UserService


class LoginDialog(QWidget):
    """登录对话框"""

    loginSuccess = Signal(object)  # 登录成功信号，传递 User 对象

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_service = UserService(db)
        self.current_user = None
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 标题
        title = SubtitleLabel("VoidView - 视频质量评测系统", self)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 用户名
        self.usernameEdit = LineEdit(self)
        self.usernameEdit.setPlaceholderText("用户名")
        self.usernameEdit.setClearButtonEnabled(True)
        layout.addWidget(self.usernameEdit)

        # 密码
        self.passwordEdit = LineEdit(self)
        self.passwordEdit.setPlaceholderText("密码")
        self.passwordEdit.setEchoMode(LineEdit.Password)
        self.passwordEdit.setClearButtonEnabled(True)
        layout.addWidget(self.passwordEdit)

        # 登录按钮
        self.loginBtn = PrimaryPushButton("登录", self)
        self.loginBtn.clicked.connect(self.attemptLogin)
        layout.addWidget(self.loginBtn)

        # 回车登录
        self.passwordEdit.returnPressed.connect(self.attemptLogin)

        layout.addStretch()

    def attemptLogin(self):
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text()

        if not username or not password:
            InfoBar.warning("提示", "请输入用户名和密码", self)
            return

        user = self.user_service.authenticate(username, password)
        if user:
            self.current_user = user

            # 检查是否需要修改密码
            if user.must_change_password:
                self.showChangePasswordDialog()
            else:
                self.loginSuccess.emit(user)
        else:
            InfoBar.error("错误", "用户名或密码错误", self)
            self.passwordEdit.clear()

    def showChangePasswordDialog(self):
        """显示修改密码对话框"""
        # 实现修改密码逻辑...
        pass


class ChangePasswordDialog(MessageBox):
    """修改密码对话框"""

    def __init__(self, user, user_service, parent=None):
        super().__init__("修改密码", "", parent)
        self.user = user
        self.user_service = user_service

        # 添加密码输入框
        self.oldPasswordEdit = LineEdit(self)
        self.oldPasswordEdit.setEchoMode(LineEdit.Password)
        self.oldPasswordEdit.setPlaceholderText("当前密码")

        self.newPasswordEdit = LineEdit(self)
        self.newPasswordEdit.setEchoMode(LineEdit.Password)
        self.newPasswordEdit.setPlaceholderText("新密码")

        self.confirmPasswordEdit = LineEdit(self)
        self.confirmPasswordEdit.setEchoMode(LineEdit.Password)
        self.confirmPasswordEdit.setPlaceholderText("确认新密码")

        self.viewLayout.addWidget(self.oldPasswordEdit)
        self.viewLayout.addWidget(self.newPasswordEdit)
        self.viewLayout.addWidget(self.confirmPasswordEdit)

        self.yesButton.setText("确认修改")
        self.cancelButton.setText("取消")

    def validate(self) -> bool:
        if not self.user.verify_password(self.oldPasswordEdit.text()):
            InfoBar.error("错误", "当前密码错误", self)
            return False

        new_pwd = self.newPasswordEdit.text()
        if len(new_pwd) < 6:
            InfoBar.error("错误", "密码长度不能少于6位", self)
            return False

        if new_pwd != self.confirmPasswordEdit.text():
            InfoBar.error("错误", "两次输入的密码不一致", self)
            return False

        return True
```

### 权限控制装饰器

```python
# src/utils/auth.py
from functools import wraps
from typing import Callable
from core.models.user import User, UserRole


def require_root(func: Callable) -> Callable:
    """装饰器: 要求 root 权限"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'current_user') or not self.current_user:
            raise PermissionError("请先登录")
        if not self.current_user.is_root():
            from qfluentwidgets import InfoBar
            InfoBar.error("权限不足", "此操作需要管理员权限", self)
            return None
        return func(self, *args, **kwargs)
    return wrapper


# 使用示例
class UserManagementPage(QWidget):
    def __init__(self, current_user: User, db, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.db = db

    @require_root
    def createNewUser(self):
        """创建新用户 - 仅 root 可调用"""
        # 创建用户逻辑...
        pass
```

### 全局用户状态

```python
# src/app/app_state.py
from typing import Optional
from core.models.user import User


class AppState:
    """全局应用状态 (单例)"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_user = None
        return cls._instance

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def set_user(self, user: User):
        self._current_user = user

    def logout(self):
        self._current_user = None

    def is_root(self) -> bool:
        return self._current_user and self._current_user.is_root()


# 使用
app_state = AppState()
```

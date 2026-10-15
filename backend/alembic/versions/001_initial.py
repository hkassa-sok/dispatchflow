"""Initial schema; frozen independently of application models."""
from alembic import op
import sqlalchemy as sa
revision = "001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("customers",sa.Column("id",sa.Integer,primary_key=True),sa.Column("name",sa.String(100),nullable=False))
    op.create_table("merchants",sa.Column("id",sa.Integer,primary_key=True),sa.Column("name",sa.String(100),nullable=False),sa.Column("lat",sa.Float,nullable=False),sa.Column("lng",sa.Float,nullable=False))
    op.create_table("drivers",sa.Column("id",sa.Integer,primary_key=True),sa.Column("name",sa.String(100),nullable=False),sa.Column("available",sa.Boolean,nullable=False),sa.Column("lat",sa.Float,nullable=False),sa.Column("lng",sa.Float,nullable=False),sa.CheckConstraint("lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180"))
    op.create_index("ix_drivers_available","drivers",["available"])
    op.create_table("orders",sa.Column("id",sa.Integer,primary_key=True),sa.Column("customer_id",sa.Integer,sa.ForeignKey("customers.id"),nullable=False),sa.Column("merchant_id",sa.Integer,sa.ForeignKey("merchants.id"),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("lat",sa.Float,nullable=False),sa.Column("lng",sa.Float,nullable=False),sa.Column("prep_minutes",sa.Float,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint("status IN ('CREATED','ACCEPTED','PREPARING','READY_FOR_PICKUP','PICKED_UP','DELIVERED','CANCELLED')"),sa.CheckConstraint("prep_minutes >= 0"),sa.CheckConstraint("lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180"))
    for column in ["customer_id","merchant_id","status"]:
        op.create_index("ix_orders_"+column,"orders",[column])
    op.create_table("assignments",sa.Column("id",sa.Integer,primary_key=True),sa.Column("order_id",sa.Integer,sa.ForeignKey("orders.id"),nullable=False),sa.Column("driver_id",sa.Integer,sa.ForeignKey("drivers.id"),nullable=False),sa.Column("active",sa.Boolean,nullable=False),sa.Column("accepted",sa.Boolean,nullable=False),sa.Column("score",sa.Float,nullable=False))
    for column in ["order_id","driver_id"]:
        op.create_index("ix_assignments_"+column,"assignments",[column])
    op.create_index("uq_active_driver","assignments",["driver_id"],unique=True,postgresql_where=sa.text("active = true"),sqlite_where=sa.text("active = 1"))
    op.create_index("uq_active_order","assignments",["order_id"],unique=True,postgresql_where=sa.text("active = true"),sqlite_where=sa.text("active = 1"))

def downgrade():
    for table in ["assignments","orders","drivers","merchants","customers"]:
        op.drop_table(table)

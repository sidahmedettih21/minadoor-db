"""Initial migration

Revision ID: 001
Revises: None
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='agent'),
        sa.Column('preferred_lang', sa.String(5), nullable=True, server_default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'travel_types',
        sa.Column('id', sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(30), nullable=False),
        sa.Column('name_en', sa.String(100), nullable=False),
        sa.Column('name_fr', sa.String(100), nullable=False),
        sa.Column('name_ar', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    op.create_table(
        'clients',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('surname', sa.String(100), nullable=False),
        sa.Column('given_name', sa.String(100), nullable=False),
        sa.Column('father_name', sa.String(100), nullable=False),
        sa.Column('mother_name', sa.String(100), nullable=True),
        sa.Column('passport_number', sa.String(30), nullable=False),
        sa.Column('nationality', sa.String(50), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('passport_issue_date', sa.Date(), nullable=True),
        sa.Column('passport_expiry', sa.Date(), nullable=True),
        sa.Column('gender', sa.CHAR(1), nullable=True),
        sa.Column('travel_type_id', sa.SmallInteger(), nullable=False),
        sa.Column('payment_method', sa.String(30), nullable=True, server_default='cash'),
        sa.Column('travel_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.CheckConstraint("gender IN ('M','F')", name='check_gender'),
        sa.CheckConstraint("status IN ('active','completed','cancelled','pending')", name='check_status'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['travel_type_id'], ['travel_types.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )

    # DB-level updated_at trigger (not relying on SQLAlchemy onupdate)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_clients_updated_at
        BEFORE UPDATE ON clients
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    """)

    # Indexes
    op.create_index('idx_clients_names', 'clients', ['surname', 'given_name', 'father_name'],
                    postgresql_using='gin',
                    postgresql_ops={
                        'surname': 'gin_trgm_ops',
                        'given_name': 'gin_trgm_ops',
                        'father_name': 'gin_trgm_ops',
                    })
    op.create_index('idx_clients_passport', 'clients', ['passport_number'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_status', 'clients', ['status'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_travel_date', 'clients', ['travel_date'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_travel_type', 'clients', ['travel_type_id'],
                    postgresql_where=sa.text('NOT archived'))

    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(20), nullable=True),
        sa.Column('table_name', sa.String(50), nullable=True),
        sa.Column('record_id', sa.BigInteger(), nullable=True),
        sa.Column('old_data', postgresql.JSONB(), nullable=True),
        sa.Column('new_data', postgresql.JSONB(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Fixed: use op.execute instead of broken op.bulk_insert with string table name
    op.execute("""
        INSERT INTO travel_types (code, name_en, name_fr, name_ar) VALUES
        ('cash_umrah',       'Cash Umrah',         'Omra au comptant',       'عمرة نقدًا'),
        ('cash_hajj',        'Cash Hajj',          'Hajj au comptant',       'حج نقدًا'),
        ('instalment_umrah', 'Instalment Umrah',   'Omra à tempérament',     'عمرة بالتقسيط'),
        ('instalment_hajj',  'Instalment Hajj',    'Hajj à tempérament',     'حج بالتقسيط'),
        ('organised_travel', 'Organised Travel',   'Voyage organisé',        'سفر منظم')
    """)

    # Seed admin user – password is CHANGE_ME (hash: bcrypt of "CHANGE_ME_ADMIN_PASSWORD")
    # NOTE: manage.py handles real admin seeding from ADMIN_PASSWORD env var.
    # This hash is a placeholder; manage.py must be run post-deploy to set a real password.
    op.execute("""
        INSERT INTO users (email, password_hash, full_name, role, preferred_lang, is_active)
        VALUES ('admin@minadoor.com', '$2b$12$placeholder_run_manage_py', 'Admin User', 'admin', 'en', true)
        ON CONFLICT (email) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_clients_updated_at ON clients")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at")
    op.drop_table('audit_log')
    op.drop_index('idx_clients_travel_type', table_name='clients')
    op.drop_index('idx_clients_travel_date', table_name='clients')
    op.drop_index('idx_clients_status', table_name='clients')
    op.drop_index('idx_clients_passport', table_name='clients')
    op.drop_index('idx_clients_names', table_name='clients')
    op.drop_table('clients')
    op.drop_table('travel_types')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

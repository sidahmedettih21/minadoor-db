"""Initial migration

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table('users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('preferred_lang', sa.String(length=5), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_table('travel_types',
        sa.Column('id', sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=False),
        sa.Column('name_fr', sa.String(length=100), nullable=False),
        sa.Column('name_ar', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    op.create_table('clients',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('surname', sa.String(length=100), nullable=False),
        sa.Column('given_name', sa.String(length=100), nullable=False),
        sa.Column('father_name', sa.String(length=100), nullable=False),
        sa.Column('mother_name', sa.String(length=100), nullable=True),
        sa.Column('passport_number', sa.String(length=30), nullable=False),
        sa.Column('nationality', sa.String(length=50), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('passport_issue_date', sa.Date(), nullable=True),
        sa.Column('passport_expiry', sa.Date(), nullable=True),
        sa.Column('gender', sa.CHAR(length=1), nullable=True),
        sa.Column('travel_type_id', sa.SmallInteger(), nullable=False),
        sa.Column('payment_method', sa.String(length=30), nullable=True),
        sa.Column('travel_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=True),
        sa.CheckConstraint("gender IN ('M','F')", name='check_gender'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['travel_type_id'], ['travel_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_clients_names', 'clients', ['surname', 'given_name', 'father_name'],
                    postgresql_using='gin',
                    postgresql_ops={'surname': 'gin_trgm_ops', 'given_name': 'gin_trgm_ops', 'father_name': 'gin_trgm_ops'})
    op.create_index('idx_clients_passport', 'clients', ['passport_number'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_status', 'clients', ['status'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_travel_date', 'clients', ['travel_date'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_travel_type', 'clients', ['travel_type_id'],
                    postgresql_where=sa.text('NOT archived'))

    op.create_table('audit_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=True),
        sa.Column('table_name', sa.String(length=50), nullable=True),
        sa.Column('record_id', sa.BigInteger(), nullable=True),
        sa.Column('old_data', postgresql.JSONB(), nullable=True),
        sa.Column('new_data', postgresql.JSONB(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Seed travel types
    op.bulk_insert('travel_types', [
        {'code': 'cash_umrah', 'name_en': 'Cash Umrah', 'name_fr': 'Omra au comptant', 'name_ar': 'عمرة نقدًا'},
        {'code': 'cash_hajj', 'name_en': 'Cash Hajj', 'name_fr': 'Hajj au comptant', 'name_ar': 'حج نقدًا'},
        {'code': 'instalment_umrah', 'name_en': 'Instalment Umrah', 'name_fr': 'Omra à tempérament', 'name_ar': 'عمرة بالتقسيط'},
        {'code': 'instalment_hajj', 'name_en': 'Instalment Hajj', 'name_fr': 'Hajj à tempérament', 'name_ar': 'حج بالتقسيط'},
        {'code': 'organised_travel', 'name_en': 'Organised Travel', 'name_fr': 'Voyage organisé', 'name_ar': 'سفر منظم'},
    ])

    # Seed admin user (password: admin123)
    op.execute("""
        INSERT INTO users (email, password_hash, full_name, role, preferred_lang, is_active)
        VALUES ('admin@minadoor.com', '$2b$12$SaAzvfXNb5SHL24wciXIGOngpnTxtttW8wpSjJ4iEJsZhfJnJe9RW', 'Admin User', 'admin', 'en', true)
    """)


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_index('idx_clients_travel_type', table_name='clients')
    op.drop_index('idx_clients_travel_date', table_name='clients')
    op.drop_index('idx_clients_status', table_name='clients')
    op.drop_index('idx_clients_passport', table_name='clients')
    op.drop_index('idx_clients_names', table_name='clients')
    op.drop_table('clients')
    op.drop_table('travel_types')
    op.drop_table('users')

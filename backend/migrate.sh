#!/bin/bash
# ============================================================
#  AYUSH India AI — Database Migration
#  Migrates data from JSON/CSV files into PostgreSQL
#
#  Usage:
#    ./migrate.sh              Full migration (drop + recreate + seed)
#    ./migrate.sh --fresh      Same as above (explicit)
#    ./migrate.sh --seed-only  Keep existing data, only add missing seeds
#    ./migrate.sh --generate   Generate sample data + historical records
#    ./migrate.sh --status     Show current table row counts
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="fresh"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --fresh)      MODE="fresh"; shift ;;
        --seed-only)  MODE="seed"; shift ;;
        --generate)   MODE="generate"; shift ;;
        --status)     MODE="status"; shift ;;
        --help)
            echo "Usage: ./migrate.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fresh        Drop all tables, recreate, and migrate everything (default)"
            echo "  --seed-only    Only seed location nodes (skip drop/recreate)"
            echo "  --generate     Generate sample patients + historical data"
            echo "  --status       Show current database table row counts"
            echo "  --help         Show this help"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Activate venv ─────────────────────────────────────
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ No venv found. Run ./run.sh first to set up the environment."
    exit 1
fi

# ── Check PostgreSQL ──────────────────────────────────
if ! pg_isready -q 2>/dev/null; then
    echo "❌ PostgreSQL is not running. Start it first:"
    echo "   brew services start postgresql@16"
    exit 1
fi

# ── Check database exists ─────────────────────────────
DB_NAME="ayush_db"
if ! psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "📂 Creating database '$DB_NAME'..."
    createdb "$DB_NAME"
fi

echo ""
echo "============================================================"
echo "  AYUSH India AI — Database Migration"
echo "============================================================"

# ── Show data files found ─────────────────────────────
echo ""
echo "📁 Data files detected:"
for f in data/*.csv data/*.json ../data/*.csv ../data/*.json; do
    [ -f "$f" ] && echo "   ✓ $f"
done 2>/dev/null
echo ""

case $MODE in
    # ──────────────────────────────────────────────────
    fresh)
        echo "🔄 Mode: FRESH MIGRATION (drop + recreate + seed)"
        echo "   ⚠️  This will DELETE all existing data!"
        echo ""
        read -p "   Continue? (y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            echo "   Cancelled."
            exit 0
        fi
        echo ""
        python3 migrate_data.py
        ;;

    # ──────────────────────────────────────────────────
    seed)
        echo "🌱 Mode: SEED ONLY (keeping existing data)"
        echo ""
        python3 -c "
from database import engine, Base, SessionLocal
import models_db
Base.metadata.create_all(bind=engine)
print('  ✓ Tables ensured')

# Seed location nodes if empty
db = SessionLocal()
count = db.query(models_db.LocationNode).count()
if count == 0:
    from migrate_data import seed_location_nodes
    seed_location_nodes(db)
else:
    print(f'  ⏭  Location nodes already seeded ({count} rows)')
db.close()
"
        ;;

    # ──────────────────────────────────────────────────
    generate)
        echo "🧪 Mode: GENERATE SAMPLE DATA"
        echo ""

        echo "Step 1/2: Generating sample patient registrations..."
        python3 generate_data.py
        echo ""

        echo "Step 2/2: Generating historical patient records..."
        python3 generate_historical_data.py
        echo ""

        echo "✅ Sample data generation complete!"
        ;;

    # ──────────────────────────────────────────────────
    status)
        echo "📊 Mode: DATABASE STATUS"
        echo ""
        python3 -c "
from database import SessionLocal
import sqlalchemy

db = SessionLocal()
tables = [
    'patients', 'medical_records', 'health_records',
    'ayush_treatments', 'treatment_feedback',
    'public_health_trends', 'location_nodes',
    'disease_spread_predictions'
]
print('  Table                         Rows')
print('  ' + '-' * 45)
total = 0
for t in tables:
    try:
        result = db.execute(sqlalchemy.text(f'SELECT count(*) FROM {t}'))
        count = result.scalar()
        total += count
        print(f'  {t:30s} {count:>6}')
    except Exception as e:
        print(f'  {t:30s} ERROR')
print('  ' + '-' * 45)
print(f'  {\"TOTAL\":30s} {total:>6}')
db.close()
"
        ;;
esac

echo ""
echo "============================================================"
echo "  ✅ Done!"
echo "============================================================"

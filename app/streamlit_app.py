import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# ----- CONFIG ---------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://bduser:bdpass@localhost:5432/bd"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

st.set_page_config(page_title="BD Database", layout="wide")
st.title("BD Database — CRUD + Dashboard")

tab_dash, tab_records, tab_touchpoints, tab_admin = st.tabs(
    ["📊 Dashboard", "🗂️ Records", "🕒 Touchpoints", "⚙️ Admin"]
)

# ----- HELPER ---------------------------------------------------------------
def df(q, params=None):
    """Esegue query e ritorna DataFrame"""
    with engine.begin() as conn:
        return pd.read_sql(text(q), conn, params=params)


def exec_(q, params=None):
    """Esegue statement con commit immediato"""
    with engine.begin() as conn:
        conn.execute(text(q), params or {})

# --------------------------------------------------------------------------- #
#                                🗂️  RECORDS                                  #
# --------------------------------------------------------------------------- #
with tab_records:
    st.subheader("Records")

    # --- Filtri tabella -----------------------------------------------------
    companies = df("SELECT company_id, name FROM company ORDER BY name")
    company_filter = st.selectbox(
        "Company",
        ["(all)"] + companies["name"].tolist(),
        index=0
    )
    status_lu = df("SELECT status_id, label FROM status_lu ORDER BY label")
    status_filter = st.selectbox(
        "Status",
        ["(all)"] + status_lu["label"].tolist(),
        index=0
    )

    base_q = """
    SELECT r.record_id,
           c.name                AS company,
           pa.name               AS product_asset,
           os.label              AS outcome_sentiment,
           bm.label              AS business_mode,
           pd.label              AS primary_domain,
           sb.label              AS strategic_bucket,
           ad.label              AS application_domain,
           st.label              AS status
    FROM record r
    JOIN company             c  ON c.company_id = r.company_id
    LEFT JOIN product_asset  pa ON pa.product_asset_id = r.product_asset_id
    LEFT JOIN outcome_sentiment os ON os.outcome_sentiment_id = r.outcome_sentiment_id
    LEFT JOIN business_mode  bm ON bm.business_mode_id   = r.business_mode_id
    LEFT JOIN primary_domain pd ON pd.primary_domain_id  = r.primary_domain_id
    LEFT JOIN strategic_bucket sb ON sb.strategic_bucket_id = r.strategic_bucket_id
    LEFT JOIN application_domain ad ON ad.application_domain_id = r.application_domain_id
    LEFT JOIN status_lu      st ON st.status_id          = r.status_id
    WHERE 1=1
    """
    params = {}
    if company_filter != "(all)":
        base_q += " AND c.name = :cname"
        params["cname"] = company_filter
    if status_filter != "(all)":
        base_q += " AND st.label = :slabel"
        params["slabel"] = status_filter
    base_q += " ORDER BY c.name, r.record_id"

    st.dataframe(df(base_q, params), use_container_width=True)

    # --- Form nuovo record --------------------------------------------------
    st.markdown("---")
    st.subheader("Nuovo Record")

    col1, col2 = st.columns(2)

    # --- colonna 1: company / asset ----------------------------------------
    with col1:
        company_sel = st.selectbox(
            "Company",
            ["(nuova)"] + companies["name"].tolist()
        )
        new_company = (
            st.text_input("Nuova Company")
            if company_sel == "(nuova)" else None
        )

        # Asset dipende dalla company scelta (anche nuova)
        if company_sel == "(nuova)":
            assets_df = pd.DataFrame({"name": []})
        else:
            assets_df = df(
                """
                SELECT pa.name
                FROM product_asset pa
                JOIN company c ON c.company_id = pa.company_id
                WHERE c.name = :n
                ORDER BY pa.name
                """,
                {"n": company_sel}
            )

        pa_name = st.selectbox(
            "Product/Asset",
            ["(nuovo)"] + assets_df["name"].tolist()
        )
        new_pa = (
            st.text_input("Nuovo Product/Asset")
            if pa_name == "(nuovo)" else None
        )

    # --- colonna 2: lookup --------------------------------------------------
    with col2:
        bm_df  = df("SELECT business_mode_id, label FROM business_mode ORDER BY label")
        os_df  = df("SELECT outcome_sentiment_id, label FROM outcome_sentiment ORDER BY label")
        pd_df  = df("SELECT primary_domain_id, label FROM primary_domain ORDER BY label")
        sb_df  = df("SELECT strategic_bucket_id, label FROM strategic_bucket ORDER BY label")
        ad_df  = df("SELECT application_domain_id, label FROM application_domain ORDER BY label")
        st_df  = df("SELECT status_id, label FROM status_lu ORDER BY label")

        bm_label = st.selectbox("Business Mode", bm_df["label"])
        os_label = st.selectbox("Outcome/Sentiment", os_df["label"])
        pd_label = st.selectbox("Primary Domain", pd_df["label"])
        sb_label = st.selectbox("Strategic Bucket", sb_df["label"])
        ad_label = st.selectbox("Application Domain", ad_df["label"])
        st_label = st.selectbox("Status", st_df["label"])

    # --- Salva --------------------------------------------------------------
    if st.button("Salva Record"):
        # --- Company --------------------------------------------------------
        if company_sel == "(nuova)":
            if not new_company:
                st.error("Inserisci il nome della nuova Company")
                st.stop()
            exec_(
                "INSERT INTO company(name) VALUES (:n) "
                "ON CONFLICT (name) DO NOTHING",
                {"n": new_company}
            )
            comp_id = int(
                df("SELECT company_id FROM company WHERE name=:n", {"n": new_company})
                .iloc[0, 0]
            )
        else:
            comp_id = int(
                companies.loc[companies["name"] == company_sel, "company_id"]
            )

        # --- Product / Asset ------------------------------------------------
        if pa_name == "(nuovo)":
            if not new_pa:
                st.error("Inserisci il nome del nuovo Product/Asset")
                st.stop()
            exec_(
                """
                INSERT INTO product_asset(company_id, name)
                VALUES (:c, :n)
                ON CONFLICT (company_id, name) DO NOTHING
                """,
                {"c": comp_id, "n": new_pa}
            )
            pa_id = int(
                df(
                    """
                    SELECT product_asset_id
                    FROM product_asset
                    WHERE company_id=:c AND name=:n
                    ORDER BY 1 DESC LIMIT 1
                    """,
                    {"c": comp_id, "n": new_pa}
                ).iloc[0, 0]
            )
        else:
            pa_id = int(
                df(
                    """
                    SELECT pa.product_asset_id
                    FROM product_asset pa
                    JOIN company c ON c.company_id = pa.company_id
                    WHERE c.name=:cn AND pa.name=:pn
                    """,
                    {"cn": company_sel, "pn": pa_name}
                ).iloc[0, 0]
            )

        # --- Funzione lookup ------------------------------------------------
        def id_by(table, label):
            return int(
                df(
                    f"SELECT {table}_id FROM {table} WHERE label=:l",
                    {"l": label}
                ).iloc[0, 0]
            )

        # --- Insert finale --------------------------------------------------
        vals = dict(
            company_id=comp_id,
            product_asset_id=pa_id,
            outcome_sentiment_id=id_by("outcome_sentiment", os_label),
            business_mode_id=id_by("business_mode", bm_label),
            primary_domain_id=id_by("primary_domain", pd_label),
            strategic_bucket_id=id_by("strategic_bucket", sb_label),
            application_domain_id=id_by("application_domain", ad_label),
            status_id=id_by("status_lu", st_label),
        )
        cols = ", ".join(vals.keys())
        binds = ", ".join([f":{k}" for k in vals])

        exec_(f"INSERT INTO record({cols}) VALUES ({binds})", vals)
        st.success("Record salvato ✔ — clicca Rerun (↻) per aggiornare la lista")

# --------------------------------------------------------------------------- #
#                               🕒  TOUCHPOINTS                               #
# --------------------------------------------------------------------------- #
with tab_touchpoints:
    st.subheader("Touchpoint per Record")

    recs = df(
        """
        SELECT r.record_id,
               c.name || ' – ' || COALESCE(pa.name, '(no asset)') AS label
        FROM record r
        JOIN company c ON c.company_id = r.company_id
        LEFT JOIN product_asset pa ON pa.product_asset_id = r.product_asset_id
        ORDER BY 2
        """
    )

    if recs.empty:
        st.info("Nessun record.")
    else:
        lbl = st.selectbox("Record", recs["label"])
        rec_id = int(recs.loc[recs["label"] == lbl, "record_id"])

        brs = df(
            """
            SELECT brs_id, year, quarter
            FROM business_review_session
            ORDER BY year, quarter
            """
        )
        tp_current = df(
            "SELECT brs_id FROM touchpoint WHERE record_id=:r",
            {"r": rec_id}
        )
        current = set(tp_current["brs_id"])
        edited = False

        cols = st.columns(4)
        for i, (_, row) in enumerate(brs.iterrows()):
            col = cols[i % 4]
            with col:
                label = f"Q{int(row.quarter)}-{int(row.year)}"
                key = f"{rec_id}_{row.brs_id}"
                val = st.checkbox(
                    label,
                    value=row.brs_id in current,
                    key=key
                )

                if val and row.brs_id not in current:
                    exec_(
                        "INSERT INTO touchpoint(record_id, brs_id) "
                        "VALUES (:r, :b)",
                        {"r": rec_id, "b": int(row.brs_id)}
                    )
                    edited = True

                if not val and row.brs_id in current:
                    exec_(
                        "DELETE FROM touchpoint "
                        "WHERE record_id=:r AND brs_id=:b",
                        {"r": rec_id, "b": int(row.brs_id)}
                    )
                    edited = True

        if edited:
            st.success("Touchpoint aggiornati")

# --------------------------------------------------------------------------- #
#                                 ⚙️  ADMIN                                   #
# --------------------------------------------------------------------------- #
with tab_admin:
    st.subheader("Lookups (read-only)")

    cols = st.columns(3)
    with cols[0]:
        st.write("**Business Mode**")
        st.dataframe(df("SELECT code, label FROM business_mode ORDER BY label"))
    with cols[1]:
        st.write("**Outcome/Sentiment**")
        st.dataframe(df("SELECT code, label FROM outcome_sentiment ORDER BY label"))
    with cols[2]:
        st.write("**Status**")
        st.dataframe(df("SELECT code, label FROM status_lu ORDER BY label"))

# --------------------------------------------------------------------------- #
#                                📊  DASHBOARD                                #
# --------------------------------------------------------------------------- #
with tab_dash:
    st.subheader("KPI (demo)")

    left, right = st.columns(2)

    with left:
        st.markdown("**Distribuzione Business Mode**")
        d = df(
            """
            SELECT bm.label, COUNT(*) AS n
            FROM record r
            JOIN business_mode bm ON bm.business_mode_id = r.business_mode_id
            GROUP BY bm.label
            ORDER BY n DESC
            """
        )
        st.bar_chart(d.set_index("label")["n"])

    with right:
        st.markdown("**Distribuzione Outcome/Sentiment**")
        d = df(
            """
            SELECT os.label, COUNT(*) AS n
            FROM record r
            JOIN outcome_sentiment os
                 ON os.outcome_sentiment_id = r.outcome_sentiment_id
            GROUP BY os.label
            ORDER BY n DESC
            """
        )
        st.bar_chart(d.set_index("label")["n"])

    st.markdown("---")
    st.markdown("**Touchpoint per Trimestre**")
    d = df(
        """
        SELECT brs.year || '-Q' || brs.quarter AS yq,
               COUNT(*) AS n
        FROM touchpoint tp
        JOIN business_review_session brs ON brs.brs_id = tp.brs_id
        GROUP BY yq
        ORDER BY yq
        """
    )
    st.line_chart(d.set_index("yq")["n"])

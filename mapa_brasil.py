from geobr import read_state
import geopandas as gpd
import json
import os

# --------------------------------------------------
# 0) Garante que a pasta 'geojson/' exista
# --------------------------------------------------
os.makedirs("geojson", exist_ok=True)


# --------------------------------------------------
# 1) Lê a malha das UFs (ano 2019, por exemplo)
# --------------------------------------------------
gdf_ufs = read_state(year=2019)

# --------------------------------------------------
# 2) Confirma quais colunas existem
# --------------------------------------------------
print("Colunas no GeoDataFrame das UFs:", gdf_ufs.columns.tolist())
# Deve mostrar algo como:
# ['code_state', 'name_state', 'abbrev_state', 'code_region', 'name_region', 'geometry']

# --------------------------------------------------
# 3) Seleciona apenas a sigla (abbrev_state) e a geometria
#    e renomeia 'abbrev_state' para 'sigla' para ficar coerente
# --------------------------------------------------
gdf = gdf_ufs[["abbrev_state", "geometry"]].rename(columns={"abbrev_state": "sigla"})


# ====== Abordagem A: sem usar set_index (mais simples) ======
# --------------------------------------------------
# 4A) Converte para GeoJSON (já no formato de FeatureCollection),
#     mantendo 'sigla' como coluna. Ao fazer gdf.to_json(), a 'sigla'
#     aparecerá em properties.sigla automaticamente.
# --------------------------------------------------
geojson_uf = json.loads(gdf.to_json())

# --------------------------------------------------
# 5A) Salva o GeoJSON em disco (na pasta geojson/ do seu projeto)
# --------------------------------------------------
with open("geojson/ufs_brasil.json", "w", encoding="utf-8") as f:
    json.dump(geojson_uf, f, ensure_ascii=False, indent=2)

print("Arquivo GeoJSON gerado em: geojson/ufs_brasil.json  (pela Abordagem A)")

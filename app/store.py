"""Cache em memória da última análise por dataset.

Simples e suficiente para o MVP (a persistência definitiva do resultado fica na
API principal, na tabela AnalysisResult).
"""

LATEST: dict[int, dict] = {}

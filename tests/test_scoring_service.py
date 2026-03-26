import unittest

from app.models import LeadRequest
from app.services.scoring_service import hybrid_score


class ScoringServiceTests(unittest.TestCase):
    def test_low_intent_lead_gets_penalized(self) -> None:
        lead = LeadRequest(
            name="Maria",
            city="Fortaleza",
            monthly_bill=150,
            property_type="apartamento",
            goal="so queria entender como funciona",
        )

        result = hybrid_score(
            lead,
            {"score": 8, "urgency": "alta", "recommendation": "ligar agora"},
        )

        self.assertEqual(result.response.score, 0)
        self.assertEqual(result.response.urgency, "baixa")
        self.assertEqual(
            result.response.recommendation,
            (
                "Lead em Fortaleza, Conta de luz em torno de R$ 150/mês; o que veio na mensagem: "
                "«so queria entender como funciona». Pelo WhatsApp, manda um resumo de economia/payback e confirma "
                "se é titular da conta e tipo de imóvel e se faz sentido continuar o papo. "
                "Explicar payback e rotina sem cobrar decisão na primeira mensagem; disparar material curto e só retomar "
                "se ela responder, em até 5 a 10 dias úteis — se não responder, deixa quieto e não gasta pipeline."
            ),
        )

    def test_invalid_ai_output_falls_back_safely(self) -> None:
        lead = LeadRequest(
            name="Paulo",
            city="Natal",
            monthly_bill=450,
            property_type="casa",
            goal="reduzir conta",
        )

        result = hybrid_score(
            lead,
            {"score": "not-a-number", "urgency": "urgente", "recommendation": ""},
        )

        self.assertEqual(result.ai_raw_score, None)
        self.assertEqual(result.response.score, 6)
        self.assertEqual(result.response.urgency, "baixa")
        self.assertEqual(
            result.response.recommendation,
            (
                "Lead em Natal (casa), Conta de luz em torno de R$ 450/mês. Antes de prometer prazo, fecha telhado e "
                "incidência para dimensionar o sistema, titularidade da conta e se o valor da conta justifica abrir "
                "simulação. Puxar pelo que a conta já gasta hoje e traduzir em economia mensal estimada; o que a pessoa "
                "escreveu pede resposta rápida. Usa WhatsApp em até 5 a 10 dias úteis para depois de validar, mandar "
                "simulação com os dados dela."
            ),
        )


if __name__ == "__main__":
    unittest.main()

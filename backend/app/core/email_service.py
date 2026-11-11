"""
Serviço de Disparo de E-mails (Gmail SMTP + Caixa de Saída Auditada) do Projeto Nexo.

Suporta:
1. Envio real via Gmail SMTP (`smtp.gmail.com:587` TLS) usando Senha de App do Google.
2. Persistência de cópia local em `backend/logs/outbox/` para auditoria e fallback caso
   a rede da apresentação bloqueie a porta 587 ou a Senha de App ainda não tenha sido informada.
3. Templates HTML profissionais para:
   - Confirmação de Cadastro de Conta (Gmail)
   - Código de Autenticação em Duas Etapas (2FA)
   - Código de Recuperação de Senha
   - Relatório de Auditoria 360° com Planilha Excel (`.csv`) em anexo
"""

from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import LOGS_DIR, settings
from app.core.security import now_brazil_iso

OUTBOX_DIR = LOGS_DIR / "outbox"
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
SMTP_RUNTIME_FILE = LOGS_DIR / "smtp_config.json"


def get_smtp_config() -> Dict[str, Any]:
    """Lê a configuração SMTP atual (permitindo atualização em tempo real pela interface)."""
    cfg = {
        "host": settings.NEXO_SMTP_HOST,
        "port": settings.NEXO_SMTP_PORT,
        "user": settings.NEXO_SMTP_USER,
        "password": settings.NEXO_SMTP_PASSWORD,
        "default_to": settings.NEXO_ALERT_EMAIL_TO or settings.NEXO_SMTP_USER,
    }
    if SMTP_RUNTIME_FILE.exists():
        try:
            saved = json.loads(SMTP_RUNTIME_FILE.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in saved.items() if v is not None})
        except Exception:
            pass
    return cfg


def save_smtp_config(user: str, password: str, default_to: Optional[str] = None) -> Dict[str, Any]:
    """Salva as credenciais SMTP do Gmail informadas pelo Administrador."""
    data = {
        "host": "smtp.gmail.com",
        "port": 587,
        "user": user.strip(),
        "password": password.strip().replace(" ", ""),
        "default_to": (default_to or user).strip(),
    }
    SMTP_RUNTIME_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "host": data["host"],
        "port": data["port"],
        "user": data["user"],
        "default_to": data["default_to"],
        "configured": bool(data["user"] and data["password"]),
    }


def send_nexo_email(
    *,
    to_email: str,
    subject: str,
    html_body: str,
    plain_body: str,
    attachment_filename: Optional[str] = None,
    attachment_bytes: Optional[bytes] = None,
    attachment_mime: str = "text/csv",
) -> Dict[str, Any]:
    """
    Envia um e-mail via SMTP Gmail (se configurado) e grava um registro auditável
    em `backend/logs/outbox/outbox_history.jsonl`.
    """
    cfg = get_smtp_config()
    ts = now_brazil_iso()

    msg = EmailMessage()
    sender = cfg["user"] or "no-reply@nexo.com"
    msg["Subject"] = subject
    msg["From"] = f"Projeto Nexo <{sender}>"
    msg["To"] = to_email
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    if attachment_filename and attachment_bytes is not None:
        maintype, subtype = attachment_mime.split("/", 1)
        msg.add_attachment(
            attachment_bytes,
            maintype=maintype,
            subtype=subtype,
            filename=attachment_filename,
        )

    sent_via_smtp = False
    smtp_error: Optional[str] = None

    if cfg.get("user") and cfg.get("password"):
        try:
            with smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=12) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
            sent_via_smtp = True
        except Exception as exc:
            smtp_error = str(exc)

    # Sempre salva no histórico local de e-mails para inspeção imediata
    record = {
        "timestamp": ts,
        "to": to_email,
        "from": sender,
        "subject": subject,
        "plain_body": plain_body,
        "attachment": attachment_filename,
        "sent_via_smtp": sent_via_smtp,
        "smtp_error": smtp_error,
    }
    history_file = OUTBOX_DIR / "outbox_history.jsonl"
    with history_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def list_outbox_emails(limit: int = 30) -> List[Dict[str, Any]]:
    """Lista os últimos e-mails disparados pelo sistema."""
    history_file = OUTBOX_DIR / "outbox_history.jsonl"
    if not history_file.exists():
        return []
    lines = history_file.read_text(encoding="utf-8").strip().splitlines()
    items = []
    for line in reversed(lines[-limit:]):
        try:
            items.append(json.loads(line))
        except Exception:
            pass
    return items


def send_welcome_confirmation_email(
    *,
    to_email: str,
    user_name: str,
    role: str,
    verification_code: str,
) -> Dict[str, Any]:
    role_badge = "Administrador Corporativo (Acesso Total + Logs 360°)" if role == "admin" else "Membro Nexo"
    subject = f"[Projeto Nexo] Confirmação de Cadastro — Bem-vindo(a), {user_name}!"
    plain = (
        f"Olá, {user_name}!\n\n"
        f"Sua conta no Projeto Nexo foi criada com sucesso.\n"
        f"E-mail confirmado: {to_email}\n"
        f"Nível de Acesso: {role_badge}\n"
        f"Código de Confirmação de E-mail: {verification_code}\n\n"
        f"Equipe Projeto Nexo"
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; border: 1px solid #1e3a8a; border-radius: 12px; overflow: hidden;">
      <div style="background: #0f2942; color: #ffffff; padding: 20px; text-align: center;">
        <h2 style="margin: 0;">Projeto Nexo — Confirmação de Conta</h2>
      </div>
      <div style="padding: 24px; color: #1f2937; background: #ffffff;">
        <p>Olá, <strong>{user_name}</strong>!</p>
        <p>Este e-mail confirma a criação da sua conta na plataforma <strong>Nexo</strong>.</p>
        <div style="background: #f3f4f6; padding: 14px; border-radius: 8px; margin: 16px 0;">
          <p style="margin: 4px 0;"><strong>E-mail:</strong> {to_email}</p>
          <p style="margin: 4px 0;"><strong>Perfil da Conta:</strong> {role_badge}</p>
          <p style="margin: 4px 0;"><strong>Protocolo de Verificação:</strong> <code style="font-size: 16px; color: #0284c7; font-weight: bold;">{verification_code}</code></p>
        </div>
        <p style="font-size: 12px; color: #6b7280;">Data/Hora do registro: {now_brazil_iso()}</p>
      </div>
    </div>
    """
    return send_nexo_email(to_email=to_email, subject=subject, html_body=html, plain_body=plain)


def send_2fa_code_email(*, to_email: str, user_name: str, code: str) -> Dict[str, Any]:
    subject = f"[Projeto Nexo] Seu código de verificação em 2 etapas: {code}"
    plain = (
        f"Olá, {user_name}!\n\n"
        f"Seu código de Autenticação em Duas Etapas (2FA) para entrar no Nexo é: {code}\n"
        f"Este código expira em 10 minutos.\n"
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; border: 1px solid #0284c7; border-radius: 12px; overflow: hidden;">
      <div style="background: #0f2942; color: #ffffff; padding: 18px; text-align: center;">
        <h2 style="margin: 0;">Autenticação em Duas Etapas (2FA)</h2>
      </div>
      <div style="padding: 24px; text-align: center; background: #ffffff; color: #111827;">
        <p>Olá, <strong>{user_name}</strong>! Utilize o código de segurança abaixo para concluir seu login:</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #0284c7; background: #f0f9ff; padding: 16px; border-radius: 8px; margin: 20px 0;">
          {code}
        </div>
        <p style="font-size: 12px; color: #6b7280;">Se não foi você quem tentou entrar, altere sua senha imediatamente.</p>
      </div>
    </div>
    """
    return send_nexo_email(to_email=to_email, subject=subject, html_body=html, plain_body=plain)


def send_audit_logs_excel_email(
    *,
    to_email: str,
    admin_name: str,
    csv_bytes: bytes,
    total_events: int,
) -> Dict[str, Any]:
    ts = now_brazil_iso()
    subject = f"[Projeto Nexo] Planilha de Auditoria & Logs 360° ({total_events} registros)"
    plain = (
        f"Olá, {admin_name}!\n\n"
        f"Segue em anexo a planilha atualizada de Auditoria 360° do Projeto Nexo (nexo_audit_logs.csv),\n"
        f"contendo {total_events} eventos registrados com quem fez, data/hora de Brasília, IP e estados antes/depois.\n\n"
        f"Gerado em: {ts}"
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; border: 1px solid #0f2942; border-radius: 12px; overflow: hidden;">
      <div style="background: #0f2942; color: #ffffff; padding: 20px; text-align: center;">
        <h2 style="margin: 0;">Relatório de Auditoria & Logs 360°</h2>
      </div>
      <div style="padding: 24px; background: #ffffff; color: #1f2937;">
        <p>Olá, <strong>{admin_name}</strong>!</p>
        <p>A planilha completa de auditoria do <strong>Projeto Nexo</strong> foi gerada e está anexada a este e-mail no formato compatível com o <strong>Microsoft Excel (.csv)</strong>.</p>
        <ul>
          <li><strong>Total de eventos auditados:</strong> {total_events}</li>
          <li><strong>Data/Hora da exportação:</strong> {ts}</li>
          <li><strong>Arquivo anexo:</strong> <code>nexo_audit_logs.csv</code></li>
        </ul>
      </div>
    </div>
    """
    return send_nexo_email(
        to_email=to_email,
        subject=subject,
        html_body=html,
        plain_body=plain,
        attachment_filename="nexo_audit_logs.csv",
        attachment_bytes=csv_bytes,
        attachment_mime="text/csv",
    )

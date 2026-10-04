"""Interactive CLI Interface for Indonesian Legal AI Agent.

Menggunakan Rich library untuk tampilan terminal yang elegan, interaktif, dan mudah dibaca.
"""
import sys
import argparse
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.markdown import Markdown

from engine.agent_system import LegalAgentOrchestrator
from crawler_connector.connector import CrawlerConnector

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold white on blue] ⚖️ INDONESIAN LEGAL AI AGENT - KONSULTASI HUKUM CERDAS [/bold white on blue]\n"
            "[italic cyan]Berbasis Sumber Resmi Peraturan.go.id, KUHP WvS, UU 1/2023, KUHAP, dan Putusan MK[/italic cyan]",
            border_style="cyan"
        )
    )


def display_clarification(response, user_query: str, auto_mode: bool = False) -> Dict[str, Any]:
    console.print(Panel(response.message, title="[yellow]🔍 Mode Klarifikasi Proaktif[/yellow]", border_style="yellow"))

    answers: Dict[str, Any] = {}

    for idx, q in enumerate(response.questions, 1):
        console.print(f"\n[bold green]Pertanyaan #{idx}:[/bold green] [bold white]{q.question}[/bold white]")
        console.print(f"[dim italic]Konteks Hukum: {q.context_why_needed}[/dim italic]")

        table = Table(title="Pilihan Opsi Fakta", border_style="dim")
        table.add_column("No", justify="center", style="cyan", no_wrap=True)
        table.add_column("Opsi Fakta", style="bold")
        table.add_column("Implikasi Yuridis", style="yellow")

        for opt_idx, opt in enumerate(q.options, 1):
            table.add_row(str(opt_idx), opt.label, opt.legal_implication)

        console.print(table)

        if not auto_mode and sys.stdin.isatty():
            choice = Prompt.ask(f"Pilih opsi untuk pertanyaan #{idx} (1-{len(q.options)})", default="1")
            try:
                selected_idx = int(choice) - 1
                if 0 <= selected_idx < len(q.options):
                    if q.id == "q_perencanaan":
                        answers["direncanakan"] = (selected_idx == 0)
                    elif q.id == "q_kejiwaan":
                        answers["gangguan_kejiwaan"] = (selected_idx == 1)
                    elif q.id == "q_waktu_kejadian":
                        answers["rezim_kuhp"] = "KUHP_LAMA_WVS" if selected_idx == 0 else "KUHP_BARU_UU_1_2023"
                    elif q.id == "q_prosedur_tersangka":
                        answers["alat_bukti_cukup"] = (selected_idx == 1)
                        answers["sudah_diperiksa_calon"] = (selected_idx == 1)
            except ValueError:
                pass
        else:
            console.print(f"[green]✔ [Mode Otomatis] Memilih Opsi #1: {q.options[0].label}[/green]")
            if q.id == "q_perencanaan":
                answers["direncanakan"] = True
            elif q.id == "q_kejiwaan":
                answers["gangguan_kejiwaan"] = False
            elif q.id == "q_waktu_kejadian":
                answers["rezim_kuhp"] = "KUHP_LAMA_WVS"
            elif q.id == "q_prosedur_tersangka":
                answers["alat_bukti_cukup"] = False
                answers["sudah_diperiksa_calon"] = False

    return answers


def display_assessment(assessment):
    console.print("\n" + "=" * 80)
    console.print(Panel(f"[bold cyan]Ringkasan Kasus:[/bold cyan] {assessment.case_summary}\n"
                        f"[bold yellow]Isu Hukum Pokok (Issue):[/bold yellow] {assessment.issue}",
                        title="[bold green]📑 Hasil Analisis Yuridis (Metode IRAC)[/bold green]",
                        border_style="green"))

    # Tabel Rujukan Pasal yang Diterapkan
    table = Table(title="📚 Dasar Regulasi Resmi yang Diterapkan (Rules)", border_style="cyan")
    table.add_column("Regulasi", style="cyan", no_wrap=False)
    table.add_column("Pasal / Norma", style="bold yellow")
    table.add_column("Status Keberlakuan", style="green")
    table.add_column("Bunyi Teks & Esensi Pasal", style="white")

    for article in assessment.applicable_rules:
        status_color = "green" if article.status.value == "BERLAKU" else "magenta"
        table.add_row(
            f"{article.regulation_name}\n({article.regulation_number})",
            f"Pasal {article.article_number}",
            f"[{status_color}]{article.status.value}[/{status_color}]",
            f"{article.content}\n[dim italic]Catatan: {article.notes or '-'}[/dim italic]"
        )

    console.print(table)

    # Subsumpsi & Analisis Penerapan
    console.print("\n[bold cyan]🔬 Penerapan & Subsumpsi Hukum (Application):[/bold cyan]")
    console.print(Markdown(assessment.application_analysis))

    # Alur Prosedural jika ada (misal penetapan tersangka atau tahapan regulasi)
    if assessment.procedural_steps:
        is_suspect = any(
            any(w in s.lower() for w in ["tersangka", "praperadilan", "sprindik", "penyidikan"])
            for s in assessment.procedural_steps
        ) or any(w in (assessment.issue or "").lower() for w in ["tersangka", "praperadilan"])
        title = "Alur Prosedural Penetapan Status Tersangka yang Sah" if is_suspect else "Tahapan & Alur Prosedural Hukum"
        console.print(f"\n[bold yellow]📋 {title}:[/bold yellow]")
        for step in assessment.procedural_steps:
            console.print(f"  [bold green]✔[/bold green] {step}")

    # Faktor Memberatkan & Meringankan
    if assessment.aggravating_factors:
        console.print("\n[bold red]⚠️ Faktor Memberatkan Pidana:[/bold red]")
        for f in assessment.aggravating_factors:
            console.print(f"  [red]•[/red] {f}")

    if assessment.mitigating_factors:
        console.print("\n[bold green]🛡️ Faktor Meringankan / Alasan Pemaaf:[/bold green]")
        for f in assessment.mitigating_factors:
            console.print(f"  [green]•[/green] {f}")

    # Kesimpulan Akhir
    console.print(Panel(f"[bold white]{assessment.conclusion}[/bold white]\n\n[dim]⚖️ Disclaimer: {assessment.legal_disclaimer}[/dim]",
                        title="[bold red]⚖️ KESIMPULAN YURIDIS (CONCLUSION)[/bold red]",
                        border_style="red"))


def run_single_query(orchestrator, query: str, auto_mode: bool = False):
    console.print(f"\n[bold magenta]👤 Pertanyaan Pengguna:[/bold magenta] [bold white]\"{query}\"[/bold white]\n")

    # Round 1: Fact Evaluation & Proactive Clarification Check
    response = orchestrator.process_query(query)

    if response.is_clarification_mode:
        answers = display_clarification(response, query, auto_mode=auto_mode)
        console.print("\n[bold cyan]🔄 Menyerap klarifikasi fakta dari pengguna dan memproses analisis mendalam...[/bold cyan]")
        
        # Round 2: Assessment with clarified facts
        final_response = orchestrator.process_query(query, case_context=answers, force_assessment=True)
        if final_response.assessment:
            display_assessment(final_response.assessment)
    else:
        if response.assessment:
            display_assessment(response.assessment)


def main():
    parser = argparse.ArgumentParser(description="Indonesian Legal AI Agent CLI")
    parser.add_argument("--query", "-q", type=str, help="Pertanyaan hukum")
    parser.add_argument("--demo", action="store_true", help="Jalankan demo 3 skenario hukum utama")
    parser.add_argument("--crawler-status", action="store_true", help="Cek status integrasi Peraturan-Crawler")
    parser.add_argument("--ingest-url", type=str, help="Download, ekstrak hierarkis, dan indeks UU dari URL detail peraturan.go.id")
    args = parser.parse_args()

    print_banner()

    connector = CrawlerConnector()
    orchestrator = LegalAgentOrchestrator()

    if args.ingest_url:
        from crawler_connector.pipeline import LegalDataPipeline
        pipeline = LegalDataPipeline()
        console.print(f"[bold cyan]📥 Memproses Ingestion Regulasi dari:[/bold cyan] {args.ingest_url}")
        articles = pipeline.ingest_from_detail_url(args.ingest_url)
        if articles:
            console.print(Panel(
                f"Nama Regulasi: {articles[0].regulation_name}\n"
                f"Nomor: {articles[0].regulation_number}\n"
                f"Status: {articles[0].status.value}\n"
                f"Total Pasal Berhasil Diekstrak: {len(articles)} pasal",
                title="[bold green]✅ Ingestion Sukses[/bold green]",
                border_style="green"
            ))
        else:
            console.print("[bold red]❌ Gagal mengekstrak atau mengunduh PDF dari URL tersebut.[/bold red]")
        return

    if args.crawler_status:
        stats = connector.get_crawler_stats()
        console.print(Panel(
            f"Direktori Crawler: /root/Peraturan-Crawler\n"
            f"Crawler Ditemukan: {stats['crawler_found']}\n"
            f"Metadata File: {stats['metadata_file_found']} ({stats['total_metadata_records']} entri)\n"
            f"PDF Terunduh: {stats['total_downloaded_pdfs']} file PDF",
            title="📊 Status Integrasi Peraturan-Crawler",
            border_style="cyan"
        ))
        return

    if args.demo:
        test_queries = [
            "apa hukuman bagi seorang yang membunuh kedua orang tuanya",
            "apakah seseorang yang membunuh satu keluarga bisa didakwakan/ dihukum seumur hidup?",
            "bagaimana alur polisi atau pengadilan menetapkan status tersangka pada seseorang"
        ]
        for q in test_queries:
            run_single_query(orchestrator, q, auto_mode=True)
            console.print("\n" + "-" * 80 + "\n")
        return

    if args.query:
        run_single_query(orchestrator, args.query)
    else:
        console.print("[yellow]Tips: Jalankan dengan --demo untuk menguji ketiga pertanyaan hukum yang diminta pengguna.[/yellow]")
        query = Prompt.ask("\n[bold cyan]Masukkan pertanyaan hukum Anda[/bold cyan]")
        if query:
            run_single_query(orchestrator, query)


if __name__ == "__main__":
    main()

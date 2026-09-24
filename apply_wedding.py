#!/usr/bin/env python3
"""
Wedding Template Customizer with Dual-Side (Nhà Trai / Nhà Gái) Support.
Generates:
  - nhatrai/index.html & nhatrai.html: Perfect Zalo & FB preview for Nhà Trai (Lễ Thành Hôn)
  - nhagai/index.html & nhagai.html: Perfect Zalo & FB preview for Nhà Gái (Lễ Vu Quy)
  - index.html: Root page with automatic ?side=nhagai / ?side=nhatrai detection
"""

import os
import sys
import json
import shutil
import re
from typing import List, Dict, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = BASE_DIR if os.path.exists(os.path.join(BASE_DIR, "custom_wedding")) else os.path.join(BASE_DIR, "hoangnhatthuyhang")
INDEX_HTML = os.path.join(SITE_DIR, "index.html")
ORIGINAL_HTML = os.path.join(SITE_DIR, "index.original.html")
CUSTOM_DIR = os.path.join(SITE_DIR, "custom_wedding")
CONFIG_FILE = os.path.join(CUSTOM_DIR, "info.json")
ALBUM_DIR = os.path.join(CUSTOM_DIR, "album")
IMAGES_DIR = os.path.join(SITE_DIR, "images")


def get_album_dir(config: Optional[dict] = None) -> Tuple[str, str]:
    """
    Return (full_album_path, folder_name) based on config and available directories.
    Priority:
    1. config['thu_muc_album'] if defined and exists in custom_wedding/
    2. 'album2' folder in custom_wedding/ if it exists
    3. 'album' folder in custom_wedding/
    """
    if config and config.get("thu_muc_album"):
        folder_name = config["thu_muc_album"].strip()
        custom_album = os.path.join(CUSTOM_DIR, folder_name)
        if os.path.exists(custom_album):
            return custom_album, folder_name
    album2_dir = os.path.join(CUSTOM_DIR, "album2")
    if os.path.exists(album2_dir):
        return album2_dir, "album2"
    return os.path.join(CUSTOM_DIR, "album"), "album"


# Subdirectories for dual sides
NHA_TRAI_DIR = os.path.join(SITE_DIR, "nhatrai")
NHA_GAI_DIR = os.path.join(SITE_DIR, "nhagai")
NHA_TRAI_HTML = os.path.join(SITE_DIR, "nhatrai.html")
NHA_GAI_HTML = os.path.join(SITE_DIR, "nhagai.html")

# Specific wedding photo slots in the template:
HERO_SLOT = "images/itsk2851a-20251006144830-optts.jpg"       # BOX1: Ảnh bìa lớn mở đầu thiệp
SAVEDATE_SLOT = "images/itsk2754a-20251006145138-jfgqu.jpg"   # BOX3: Ảnh Save the date / Quyết định bên nhau trọn đời
GROOM_SLOT = "images/itsk3101a-20251006145418-uz8ay.jpg"      # BOX6: Ảnh chân dung Chú rể (Bên trái, phía trên Nhà Trai)
BRIDE_SLOT = "images/itsk3191a-20251008053414-kpxv0.jpg"      # BOX5: Ảnh chân dung Cô dâu (Bên phải, phía trên Nhà Gái)
TIMELINE_SLOT = "images/itsk3091a-20251008051748-n35d5.jpg"   # BOX9: Ảnh mục Timeline / Lịch trình
QR_SLOT = "images/z7088734823475_7734a20ec0ef7860291ea3a3f8324d90-20251006153650-jjc6y.jpg"  # IMAGE50: Mã QR hiển thị trong popup

# Album photo slots in the template (Our memories & gallery):
ALBUM_PHOTO_SLOTS = [
    "images/itsk3501a-20251008052653-kbwxe.jpg",  # BOX17
    "images/itsk2885a-20251006151605-tqtdt.jpg",  # BOX18
    "images/jr1_2831-20251009082156-5w09o.jpg",   # BOX20
    "images/l1007070-20251009082244-o2mfz.jpg",   # BOX21
    "images/l1006687-20251009082317-mdujw.jpg",   # BOX22
    "images/itsk3108a-20251008052926-uueyz.jpg",   # BOX23
    "images/jrm_3276-20251009082414-vjf8e.jpg",   # BOX24
    "images/jrm_3174-20251009082430-na-l8.jpg",   # BOX25
    "images/l1006869-20251009082457-rqa6w.jpg",   # IMAGE58
    "images/itsk3233a-20251008062759-vbxj2.jpg",   # IMAGE59
    "images/jrm_4266-20251009082606-5c5jv.jpg",   # BOX26
    "images/itsk2704a2-20251006152350-jbizu.jpg", # BOX27
    "images/itsk3606a-20251009082539-ojxl9.jpg",  # BOX35
]


def find_file_with_extensions(base_names, directory: str) -> Optional[str]:
    """Find a file with common image extensions (.jpg, .jpeg, .png, .webp, etc.)."""
    if isinstance(base_names, str):
        base_names = [base_names]
    valid_exts = [".jpg", ".jpeg", ".png", ".webp", ".avif", ".JPG", ".JPEG", ".PNG", ".WEBP"]
    for bname in base_names:
        for ext in valid_exts:
            p = os.path.join(directory, f"{bname}{ext}")
            if os.path.isfile(p):
                return p
    return None


def generate_og_banners(config: dict, custom_dir: str, images_dir: str):
    """
    Tự động tạo hoặc chuẩn bị ảnh banner Open Graph (1200x630) cho Nhà Trai, Nhà Gái và Root.
    Tỉ lệ 1.91:1 (1200x630) là chuẩn vàng hiển thị full ảnh cực đẹp trên Zalo, Messenger, Facebook.
    """
    try:
        from PIL import Image, ImageFilter, ImageDraw, ImageFont
    except ImportError:
        console.print("[yellow]! Pillow chưa được cài, bỏ qua tự động tạo ảnh OG banner.[/yellow]")
        return

    # 1. Kiểm tra ảnh do người dùng chủ động bỏ vào custom_wedding/
    custom_trai = find_file_with_extensions(["og_nhatrai", "og_trai"], custom_dir)
    custom_gai = find_file_with_extensions(["og_nhagai", "og_gai"], custom_dir)
    custom_root = find_file_with_extensions(["og_share", "og", "share"], custom_dir)

    if custom_trai:
        shutil.copyfile(custom_trai, os.path.join(images_dir, "og_nhatrai.jpg"))
    if custom_gai:
        shutil.copyfile(custom_gai, os.path.join(images_dir, "og_nhagai.jpg"))
    if custom_root:
        shutil.copyfile(custom_root, os.path.join(images_dir, "og_share.jpg"))

    # 2. Nếu thiếu, tự động tạo từ ảnh org/hero/album với layout thiệp vàng sang trọng
    hero_photo = (
        find_file_with_extensions(["org", "og_photo"], custom_dir)
        or (os.path.join(BASE_DIR, "org.jpeg") if os.path.exists(os.path.join(BASE_DIR, "org.jpeg")) else None)
        or find_file_with_extensions(["hero", "banner"], custom_dir)
        or os.path.join(images_dir, "custom_hero.jpeg")
    )
    if not hero_photo or not os.path.exists(hero_photo):
        return

    font_candidates = [
        os.path.join(BASE_DIR, "fonts", "cormorantinfant-medium-20250320040935-nh0vi.ttf"),
        os.path.join(SITE_DIR, "fonts", "cormorantinfant-medium-20250320040935-nh0vi.ttf"),
        os.path.join(BASE_DIR, "fonts", "ebgaramond-medium-20250320040915-omeex.ttf"),
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)

    def create_single_banner(photo_path, le_title, names, time_str, venue, address, out_path):
        W, H = 1200, 630
        try:
            bg = Image.open(photo_path).convert("RGB")
        except Exception:
            return

        # Nền mờ nghệ thuật
        bg_ratio = max(W / bg.width, H / bg.height)
        new_w, new_h = int(bg.width * bg_ratio), int(bg.height * bg_ratio)
        bg_resized = bg.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        canvas = bg_resized.crop((left, top, left + W, top + H))
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=25))

        # Lớp phủ tối gradient tinh tế
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 135))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)

        # Khung ảnh sắc nét của cặp đôi bên phải
        p_h = H - 60
        p_w = int(bg.width * (p_h / bg.height))
        p_sharp = bg.resize((p_w, p_h), Image.Resampling.LANCZOS)
        p_x = W - p_w - 40
        p_y = 30
        canvas.paste(p_sharp, (p_x, p_y))

        # Viền trắng bao quanh ảnh
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([p_x - 3, p_y - 3, p_x + p_w + 3, p_y + p_h + 3], outline=(255, 255, 255, 220), width=3)

        # Chữ vàng & trắng sang trọng bên trái
        if font_path:
            try:
                f_title = ImageFont.truetype(font_path, 34)
                f_names = ImageFont.truetype(font_path, 52)
                f_date = ImageFont.truetype(font_path, 30)
                f_venue = ImageFont.truetype(font_path, 25)
                f_addr = ImageFont.truetype(font_path, 20)

                draw.text((60, 130), le_title, font=f_title, fill=(255, 215, 120))
                draw.text((60, 195), names, font=f_names, fill=(255, 255, 255))
                draw.line([(60, 280), (460, 280)], fill=(255, 215, 120), width=2)
                draw.text((60, 310), time_str, font=f_date, fill=(245, 245, 245))
                draw.text((60, 365), venue, font=f_venue, fill=(220, 220, 220))
                draw.text((60, 410), address, font=f_addr, fill=(180, 180, 180))
            except Exception:
                pass

        canvas.convert("RGB").save(out_path, "JPEG", quality=95)

    cr_short = config.get("chu_re", {}).get("ten_ngan", "HOÀNG NHẬT").title()
    cd_short = config.get("co_dau", {}).get("ten_ngan", "THÚY HẰNG").title()
    trai_ev = config.get("tiec_nha_trai", {})
    gai_ev = config.get("tiec_nha_gai", {})

    # Banner Nhà Trai
    out_trai = os.path.join(images_dir, "og_nhatrai.jpg")
    if not custom_trai:
        create_single_banner(
            hero_photo,
            trai_ev.get("tieu_de_le", "LỄ THÀNH HÔN"),
            f"{cr_short} & {cd_short}",
            f"{trai_ev.get('gio_ngan', '11:00')} • {trai_ev.get('ngay_duong_lich', '18.10.2026')} ({trai_ev.get('thu', 'Chủ Nhật').title()})",
            trai_ev.get("ten_dia_diem", "Sảnh 5 - Tiệc cưới Mipec Tây Sơn"),
            trai_ev.get("dia_chi", "229 Phố Tây Sơn, Kim Liên, Hà Nội"),
            out_trai,
        )

    # Banner Nhà Gái
    out_gai = os.path.join(images_dir, "og_nhagai.jpg")
    if not custom_gai:
        create_single_banner(
            hero_photo,
            gai_ev.get("tieu_de_le", "LỄ VU QUY"),
            f"{cr_short} & {cd_short}",
            f"{gai_ev.get('gio_ngan', '16:30')} • {gai_ev.get('ngay_duong_lich', '17.10.2026')} ({gai_ev.get('thu', 'Thứ Bảy').title()})",
            gai_ev.get("ten_dia_diem", "Tư gia Nhà Gái"),
            gai_ev.get("dia_chi", "Thọ Vực, Xã Xuân Giang, Tỉnh Ninh Bình"),
            out_gai,
        )

    # Banner Root
    out_root = os.path.join(images_dir, "og_share.jpg")
    if not custom_root:
        create_single_banner(
            hero_photo,
            trai_ev.get("tieu_de_le", "LỄ THÀNH HÔN"),
            f"{cr_short} & {cd_short}",
            f"{trai_ev.get('ngay_duong_lich', '18.10.2026')} ({trai_ev.get('thu', 'Chủ Nhật').title()})",
            trai_ev.get("ten_dia_diem", "Sảnh 5 - Tiệc cưới Mipec Tây Sơn"),
            "Trân trọng kính mời quý khách tới chung vui!",
            out_root,
        )


def reset_to_original():
    """Reset all generated files back to clean state."""
    if not os.path.exists(ORIGINAL_HTML):
        console.print("[bold red]Lỗi:[/bold red] Không tìm thấy file gốc `index.original.html`!")
        sys.exit(1)

    shutil.copyfile(ORIGINAL_HTML, INDEX_HTML)

    # Clean subdirectories and dual-side files
    for p in [NHA_TRAI_DIR, NHA_GAI_DIR]:
        if os.path.exists(p):
            shutil.rmtree(p)

    for f in [NHA_TRAI_HTML, NHA_GAI_HTML]:
        if os.path.exists(f):
            os.remove(f)

    console.print("[bold green]✓ Đã khôi phục thành công giao diện về mẫu gốc ban đầu![/bold green]")
    console.print(f"[dim]File đã được reset: {INDEX_HTML}[/dim]\n")


def prepare_custom_images(album_dir: Optional[str] = None) -> Tuple[Dict[str, str], int, list]:
    """
    Process custom images in custom_wedding/ and custom_wedding/album/ (or album2/).
    Returns a dictionary mapping old slot URLs -> new image URLs, count of replaced slots, and list of album files.
    """
    if not album_dir:
        album_dir, _ = get_album_dir()
    slot_mapping: Dict[str, str] = {}
    replaced_count = 0

    # 1. Hero banner
    hero_file = find_file_with_extensions(["hero", "banner"], CUSTOM_DIR)
    if hero_file:
        dest_hero = f"custom_hero{os.path.splitext(hero_file)[1].lower()}"
        shutil.copyfile(hero_file, os.path.join(IMAGES_DIR, dest_hero))
        slot_mapping[HERO_SLOT] = f"images/{dest_hero}"
        replaced_count += 1

    # 2. Save the date / Quyết định bên nhau trọn đời
    savedate_file = find_file_with_extensions(["savedate", "couple", "savethedate", "save_the_date"], CUSTOM_DIR)
    if savedate_file:
        dest_savedate = f"custom_savedate{os.path.splitext(savedate_file)[1].lower()}"
        shutil.copyfile(savedate_file, os.path.join(IMAGES_DIR, dest_savedate))
        slot_mapping[SAVEDATE_SLOT] = f"images/{dest_savedate}"
        replaced_count += 1

    # 3. Chú rể
    groom_file = find_file_with_extensions(["groom", "chure", "chu_re"], CUSTOM_DIR)
    if groom_file:
        dest_groom = f"custom_groom{os.path.splitext(groom_file)[1].lower()}"
        shutil.copyfile(groom_file, os.path.join(IMAGES_DIR, dest_groom))
        slot_mapping[GROOM_SLOT] = f"images/{dest_groom}"
        replaced_count += 1

    # 4. Cô dâu
    bride_file = find_file_with_extensions(["bride", "codau", "co_dau"], CUSTOM_DIR)
    if bride_file:
        dest_bride = f"custom_bride{os.path.splitext(bride_file)[1].lower()}"
        shutil.copyfile(bride_file, os.path.join(IMAGES_DIR, dest_bride))
        slot_mapping[BRIDE_SLOT] = f"images/{dest_bride}"
        replaced_count += 1

    # 5. Timeline
    timeline_file = find_file_with_extensions(["timeline", "lich_trinh"], CUSTOM_DIR)
    if timeline_file:
        dest_timeline = f"custom_timeline{os.path.splitext(timeline_file)[1].lower()}"
        shutil.copyfile(timeline_file, os.path.join(IMAGES_DIR, dest_timeline))
        slot_mapping[TIMELINE_SLOT] = f"images/{dest_timeline}"
        replaced_count += 1

    # 6. Remaining slots: fill from album_dir
    album_photos = []
    if os.path.exists(album_dir):
        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".JPG", ".JPEG", ".PNG", ".WEBP"}
        for f in os.listdir(album_dir):
            _, ext = os.path.splitext(f)
            if ext.lower() in valid_exts:
                album_photos.append(os.path.join(album_dir, f))

        def natural_sort_key(filename):
            match = re.search(r'\d+', os.path.basename(filename))
            return int(match.group()) if match else 0

        album_photos.sort(key=natural_sort_key)

    total_album_photos = len(album_photos)

    if album_photos:
        unfilled_slots = []
        if SAVEDATE_SLOT not in slot_mapping:
            unfilled_slots.append(SAVEDATE_SLOT)
        if GROOM_SLOT not in slot_mapping:
            unfilled_slots.append(GROOM_SLOT)
        if BRIDE_SLOT not in slot_mapping:
            unfilled_slots.append(BRIDE_SLOT)
        if TIMELINE_SLOT not in slot_mapping:
            unfilled_slots.append(TIMELINE_SLOT)

        remaining_slots = unfilled_slots + ALBUM_PHOTO_SLOTS
        num_photos = len(album_photos)
        for i, old_slot in enumerate(remaining_slots):
            chosen = album_photos[i % num_photos]
            ext = os.path.splitext(chosen)[1].lower()
            dest_name = f"custom_photo_{i + 1}{ext}"
            dest_path = os.path.join(IMAGES_DIR, dest_name)
            shutil.copyfile(chosen, dest_path)
            slot_mapping[old_slot] = f"images/{dest_name}"
            replaced_count += 1

    album_files = [os.path.basename(p) for p in album_photos]
    return slot_mapping, replaced_count, album_files




DAY_ELEMENT_MAP = {
    1: "HEADLINE102", 2: "HEADLINE103", 3: "HEADLINE104", 4: "HEADLINE105",
    5: "HEADLINE106", 6: "HEADLINE107", 7: "HEADLINE108", 8: "HEADLINE109",
    9: "HEADLINE110", 10: "HEADLINE111", 11: "HEADLINE112", 12: "HEADLINE113",
    13: "HEADLINE114", 14: "HEADLINE115", 15: "HEADLINE116", 16: "HEADLINE117",
    17: "HEADLINE133", 18: "HEADLINE134", 19: "HEADLINE135", 20: "HEADLINE136",
    21: "HEADLINE137", 22: "HEADLINE138", 23: "HEADLINE139", 24: "HEADLINE126",
    25: "HEADLINE127", 26: "HEADLINE128", 27: "HEADLINE129", 28: "HEADLINE130",
    29: "HEADLINE131", 30: "HEADLINE132", 31: "HEADLINE118",
}

COL_LEFTS = [37.5, 90.25, 143.0, 195.75, 248.5, 301.25, 354.0]
ROW_TOPS = [155.45, 190.25, 227.25, 264.25, 304.25, 342.25]


def generate_calendar_css(year: int, month: int, wedding_day: int) -> str:
    """Generate exact pixel coordinates for calendar days and the heart selector."""
    import calendar
    month_cal = calendar.monthcalendar(year, month)
    num_days = calendar.monthrange(year, month)[1]
    rules = []
    heart_top, heart_left = None, None

    for row_idx, week in enumerate(month_cal):
        top = ROW_TOPS[row_idx] if row_idx < len(ROW_TOPS) else ROW_TOPS[-1] + (row_idx - len(ROW_TOPS) + 1) * 38
        for col_idx, day in enumerate(week):
            if day == 0:
                continue
            left = COL_LEFTS[col_idx]
            elem_id = DAY_ELEMENT_MAP.get(day)
            if elem_id:
                rules.append(f"#{elem_id} {{ top: {top}px !important; left: {left}px !important; display: block !important; }}")
            if day == wedding_day:
                heart_top = top - 8.8
                heart_left = left - 7.65

    # Hide unused days if month has < 31 days
    for day in range(num_days + 1, 32):
        elem_id = DAY_ELEMENT_MAP.get(day)
        if elem_id:
            rules.append(f"#{elem_id} {{ display: none !important; }}")

    if heart_top is not None and heart_left is not None:
        rules.append(f"#IMAGE42 {{ top: {heart_top}px !important; left: {heart_left}px !important; display: block !important; opacity: 1 !important; }}")

    return "\n".join(rules)


def generate_wedding_lightbox(album_files: list, is_subfolder: bool, album_folder_name: str = "album", title: str = "Hoàng Nhật &amp; Thúy Hằng") -> str:
    prefix = f"../custom_wedding/{album_folder_name}/" if is_subfolder else f"custom_wedding/{album_folder_name}/"
    css_prefix = "../css/" if is_subfolder else "css/"
    js_prefix = "../js/" if is_subfolder else "js/"
    total_photos = len(album_files)

    slides_html = "\n".join([
        f"""        <div class="swiper-slide"><img src="{prefix}{fname}" alt="Ảnh cưới {i}" loading="lazy" /></div>"""
        for i, fname in enumerate(album_files, 1)
    ])
    thumbs_html = "\n".join([
        f"""        <div class="swiper-slide"><img src="{prefix}{fname}" alt="Thumb {i}" loading="lazy" /></div>"""
        for i, fname in enumerate(album_files, 1)
    ])


    return f"""
<!-- SWIPER CAROUSEL ASSETS -->
<link rel="stylesheet" href="{css_prefix}swiper-bundle.min.css" />
<script src="{js_prefix}swiper-bundle.min.js"></script>

<!-- FULL WEDDING ALBUM LIGHTBOX (POWERED BY SWIPER) -->
<div id="full-album-modal" class="wedding-lightbox" aria-hidden="true">
  <!-- Top Bar -->
  <div class="wl-topbar">
    <div class="wl-brand">
      <span class="wl-title">{title}</span>
      <span class="wl-counter" id="wl-counter">1 / {total_photos}</span>
    </div>
    <div class="wl-actions">
      <button type="button" class="wl-btn wl-btn-autoplay" id="wl-autoplay-btn" title="Tự động trình chiếu">
        <svg class="wl-icon-play" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
        <svg class="wl-icon-pause" viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="display:none;">
          <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
        </svg>
        <span class="wl-autoplay-text">Trình chiếu</span>
      </button>
      <button type="button" class="wl-btn wl-btn-close" id="wl-close-btn" title="Đóng (Esc)">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
  </div>

  <!-- Main Swiper Viewport -->
  <div class="wl-main-container" id="wl-main-container">
    <div class="swiper wl-main-swiper" id="wl-main-swiper">
      <div class="swiper-wrapper">
{slides_html}
      </div>
      <div class="swiper-button-prev wl-swiper-prev" id="wl-prev-btn"></div>
      <div class="swiper-button-next wl-swiper-next" id="wl-next-btn"></div>
    </div>
  </div>

  <!-- Bottom Thumbs Swiper -->
  <div class="wl-thumbs-container">
    <div class="swiper wl-thumbs-swiper" id="wl-thumbs-swiper">
      <div class="swiper-wrapper">
{thumbs_html}
      </div>
    </div>
  </div>
</div>

<style type="text/css">
.wedding-lightbox {{
  position: fixed;
  inset: 0;
  z-index: 999999;
  background: radial-gradient(circle at center, rgba(14, 20, 32, 0.97) 0%, rgba(6, 10, 18, 0.99) 100%);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s ease, visibility 0.3s ease;
  user-select: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}}
.wedding-lightbox.active {{
  opacity: 1;
  visibility: visible;
}}

/* Topbar */
.wl-topbar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: linear-gradient(to bottom, rgba(0,0,0,0.6), transparent);
  z-index: 10;
}}
.wl-brand {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.wl-title {{
  color: #fff;
  font-family: "Cormorant Infant", serif, Georgia;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}}
.wl-counter {{
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 3px 10px;
  border-radius: 20px;
  backdrop-filter: blur(8px);
}}
.wl-actions {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.wl-btn {{
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.22);
  color: #fff;
  border-radius: 30px;
  padding: 8px 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}}
.wl-btn:hover {{
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-1px);
}}
.wl-btn-close {{
  width: 40px;
  height: 40px;
  padding: 0;
  justify-content: center;
  border-radius: 50%;
}}
.wl-btn-close:hover {{
  transform: rotate(90deg) scale(1.05);
}}

/* Main Swiper */
.wl-main-container {{
  flex: 1;
  width: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-sizing: border-box;
}}
.wl-main-swiper {{
  width: 100%;
  height: 100%;
}}
.wl-main-swiper .swiper-slide {{
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  box-sizing: border-box;
}}
.wl-main-swiper .swiper-slide img {{
  max-width: 95vw;
  max-height: 74vh;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 25px 60px -10px rgba(0, 0, 0, 0.75), 0 0 0 1px rgba(255, 255, 255, 0.12);
  user-select: none;
  -webkit-user-drag: none;
}}
.wl-swiper-prev, .wl-swiper-next {{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #fff !important;
  backdrop-filter: blur(12px);
  transition: all 0.25s ease;
}}
.wl-swiper-prev:after, .wl-swiper-next:after {{
  font-size: 20px !important;
  font-weight: bold;
}}
.wl-swiper-prev:hover, .wl-swiper-next:hover {{
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.08);
  box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
}}

/* Thumbs Swiper */
.wl-thumbs-container {{
  width: 100%;
  padding: 10px 16px 14px;
  background: linear-gradient(to top, rgba(0,0,0,0.6), transparent);
  box-sizing: border-box;
}}
.wl-thumbs-swiper {{
  width: 100%;
  padding: 4px 0;
}}
.wl-thumbs-swiper .swiper-slide {{
  width: 52px !important;
  height: 66px !important;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.2);
  opacity: 0.55;
  transition: all 0.25s ease;
}}
.wl-thumbs-swiper .swiper-slide img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}
.wl-thumbs-swiper .swiper-slide-thumb-active {{
  opacity: 1;
  border-color: #e2b755;
  box-shadow: 0 0 14px rgba(226, 183, 85, 0.7);
  transform: scale(1.08) translateY(-2px);
}}

/* Mobile responsive */
@media (max-width: 600px) {{
  .wl-topbar {{ padding: 12px 14px; }}
  .wl-title {{ font-size: 16px; }}
  .wl-autoplay-text {{ display: none; }}
  .wl-btn-autoplay {{ padding: 8px; }}
  .wl-swiper-prev, .wl-swiper-next {{ width: 40px; height: 40px; }}
  .wl-swiper-prev:after, .wl-swiper-next:after {{ font-size: 16px !important; }}
  .wl-main-swiper .swiper-slide img {{ max-height: 68vh; }}
  .wl-thumbs-swiper .swiper-slide {{ width: 44px !important; height: 56px !important; }}
}}

/* Trigger button hover */
#HEADLINE75, #BOX17, #BOX18, #BOX20, #BOX21, #BOX22, #BOX23, #BOX24, #BOX25, #IMAGE58, #IMAGE59 {{
  cursor: pointer !important;
}}
#HEADLINE75:hover {{
  filter: brightness(1.2) drop-shadow(0 0 8px rgba(255,255,255,0.5));
  transform: scale(1.04);
  transition: all 0.2s ease;
}}
</style>

<script type="text/javascript">
(function() {{
  var modal = document.getElementById("full-album-modal");
  var mainSwiper = null;
  var thumbsSwiper = null;
  var isPlaying = false;

  var playBtn = document.getElementById("wl-autoplay-btn");
  var playIcon = playBtn ? playBtn.querySelector(".wl-icon-play") : null;
  var pauseIcon = playBtn ? playBtn.querySelector(".wl-icon-pause") : null;
  var autoplayText = playBtn ? playBtn.querySelector(".wl-autoplay-text") : null;
  var counter = document.getElementById("wl-counter");
  var closeBtn = document.getElementById("wl-close-btn");

  function initSwipers() {{
    if (mainSwiper) return;
    if (typeof Swiper === "undefined") return;

    thumbsSwiper = new Swiper("#wl-thumbs-swiper", {{
      spaceBetween: 8,
      slidesPerView: "auto",
      freeMode: true,
      watchSlidesProgress: true,
      centerInsufficientSlides: true,
    }});

    mainSwiper = new Swiper("#wl-main-swiper", {{
      spaceBetween: 16,
      speed: 400,
      grabCursor: true,
      resistanceRatio: 0.85,
      keyboard: {{
        enabled: true,
      }},
      navigation: {{
        nextEl: "#wl-next-btn",
        prevEl: "#wl-prev-btn",
      }},
      thumbs: {{
        swiper: thumbsSwiper,
      }},
      autoplay: {{
        delay: 3500,
        disableOnInteraction: false,
        pauseOnMouseEnter: true,
      }},
      on: {{
        init: function() {{
          this.autoplay.stop();
        }},
        slideChange: function() {{
          if (counter) counter.textContent = (this.activeIndex + 1) + " / " + this.slides.length;
        }}
      }}
    }});
  }}

  function stopAutoplay() {{
    isPlaying = false;
    if (mainSwiper && mainSwiper.autoplay) mainSwiper.autoplay.stop();
    if (playIcon) playIcon.style.display = "";
    if (pauseIcon) pauseIcon.style.display = "none";
    if (autoplayText) autoplayText.textContent = "Trình chiếu";
  }}

  function startAutoplay() {{
    isPlaying = true;
    if (mainSwiper && mainSwiper.autoplay) mainSwiper.autoplay.start();
    if (playIcon) playIcon.style.display = "none";
    if (pauseIcon) pauseIcon.style.display = "";
    if (autoplayText) autoplayText.textContent = "Tạm dừng";
  }}

  function toggleAutoplay() {{
    if (isPlaying) stopAutoplay();
    else startAutoplay();
  }}

  window.openFullAlbum = function(index) {{
    index = typeof index === "number" ? index : 0;
    initSwipers();
    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    if (mainSwiper) {{
      mainSwiper.update();
      thumbsSwiper.update();
      mainSwiper.slideTo(index, 0);
    }}
  }};

  window.closeFullAlbum = function() {{
    stopAutoplay();
    modal.classList.remove("active");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }};

  if (closeBtn) closeBtn.addEventListener("click", window.closeFullAlbum);
  if (playBtn) playBtn.addEventListener("click", function(e) {{
    e.stopPropagation();
    toggleAutoplay();
  }});

  // Close when clicking outside image slide
  var mainContainer = document.getElementById("wl-main-container");
  if (mainContainer) {{
    mainContainer.addEventListener("click", function(e) {{
      if (e.target === mainContainer || e.target.classList.contains("swiper-slide")) {{
        window.closeFullAlbum();
      }}
    }});
  }}

  // Escape key
  document.addEventListener("keydown", function(e) {{
    if (modal && modal.classList.contains("active") && e.key === "Escape") {{
      window.closeFullAlbum();
    }}
  }});

  // Capture clicks on Album photos to open lightbox
  document.addEventListener("click", function(e) {{
    var albumBox = e.target.closest("#BOX17, #BOX18, #BOX20, #BOX21, #BOX22, #BOX23, #BOX24, #BOX25, #IMAGE58, #IMAGE59");
    if (albumBox) {{
      var boxMap = {{
        "BOX17": 0, "BOX18": 1, "BOX20": 2, "BOX21": 3,
        "BOX22": 4, "BOX23": 5, "BOX24": 6, "BOX25": 7,
        "IMAGE58": 8, "IMAGE59": 9
      }};
      var idx = boxMap[albumBox.id];
      if (typeof idx === "number") {{
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        window.openFullAlbum(idx);
        return false;
      }}
    }}
  }}, true);

}})();
</script>
<!-- END FULL WEDDING ALBUM LIGHTBOX -->
"""



def render_page(
    base_html: str,
    config: dict,
    side: str,  # "trai" or "gai"
    slot_mapping: Dict[str, str],
    is_subfolder: bool = False,
    is_root: bool = False,
    total_album_photos: int = 0,
    album_files: list = None,
    album_folder_name: str = "album",
) -> str:
    """Render a customized HTML page for either Nhà Trai or Nhà Gái."""
    html = base_html

    chu_re = config.get("chu_re", {})
    co_dau = config.get("co_dau", {})

    cr_full = chu_re.get("ten_day_du", "HOÀNG QUỐC BẢO")
    cr_short = chu_re.get("ten_ngan", "QUỐC BẢO")
    cd_full = co_dau.get("ten_day_du", "TRẦN THÙY DUNG")
    cd_short = co_dau.get("ten_ngan", "THÙY DUNG")

    cr_title = cr_short.title()
    cd_title = cd_short.title()

    main_wedding_date = (config.get("ngay_cuoi_chinh") or config.get("tiec_nha_trai", {}).get("ngay_duong_lich") or "18.10.2026").strip()
    main_wedding_day = int(config.get("ngay_chinh") or config.get("tiec_nha_trai", {}).get("ngay") or 18)

    # Determine event details for this side
    if side == "gai":
        event = config.get("tiec_nha_gai") or config.get("thoi_gian_va_dia_diem", {})
        person = co_dau
        side_label = "Nhà Gái"
        le_title = event.get("tieu_de_le", "LỄ VU QUY")
        doc_title = f"{le_title} - {cr_title} &amp; {cd_title}"
        og_title = f"{le_title} - Chú rể {cr_short} & Cô dâu {cd_short}"
        popup_role = "Cô dâu"
        popup_name = co_dau.get("chu_tai_khoan") or cd_full
        qr_file = (
            find_file_with_extensions("qr_bride", CUSTOM_DIR)
            or find_file_with_extensions("qr_nhagai", CUSTOM_DIR)
            or find_file_with_extensions("qr", CUSTOM_DIR)
        )
    else:
        event = config.get("tiec_nha_trai") or config.get("thoi_gian_va_dia_diem", {})
        person = chu_re
        side_label = "Nhà Trai"
        le_title = event.get("tieu_de_le", "LỄ THÀNH HÔN")
        doc_title = f"{le_title} - {cr_title} &amp; {cd_title}"
        og_title = f"{le_title} - Chú rể {cr_short} & Cô dâu {cd_short}"
        popup_role = "Chú rể"
        popup_name = chu_re.get("chu_tai_khoan") or cr_full
        qr_file = (
            find_file_with_extensions("qr_groom", CUSTOM_DIR)
            or find_file_with_extensions("qr_nhatrai", CUSTOM_DIR)
            or find_file_with_extensions("qr", CUSTOM_DIR)
        )

    # Bank details resolution
    ten_ngan_hang = (person.get("ten_ngan_hang") or event.get("ten_ngan_hang") or "").strip()
    so_tai_khoan = (person.get("so_tai_khoan") or event.get("so_tai_khoan") or "").strip()
    chu_tai_khoan = (person.get("chu_tai_khoan") or event.get("chu_tai_khoan") or popup_name).strip()

    # Legacy fallback for old single string
    legacy_stk = (person.get("ngan_hang_va_stk") or event.get("ngan_hang_va_stk") or "").strip()
    if not ten_ngan_hang and not so_tai_khoan and legacy_stk:
        parts = legacy_stk.split()
        if len(parts) >= 2:
            ten_ngan_hang = parts[0]
            so_tai_khoan = " ".join(parts[1:])
        else:
            so_tai_khoan = legacy_stk

    # Check gift button visibility config
    show_gift_cfg = event.get("hien_nut_mung_cuoi", config.get("hien_nut_mung_cuoi", True))
    has_bank_info = bool(so_tai_khoan or ten_ngan_hang)
    hide_gift_button = (not show_gift_cfg) or (not has_bank_info)

    # 1. Update Title & Open Graph Meta Tags (Bắt buộc dùng Absolute URL để Zalo & Messenger hiển thị ảnh)
    venue_name = event.get("ten_dia_diem", "Trống Đồng Palace")
    venue_addr = event.get("dia_chi", "")
    date_str = event.get("ngay_duong_lich", "15.12.2025")
    time_short = event.get("gio_ngan", "17:30")
    time_long = event.get("gio_to_chuc", "17 giờ 30 phút")
    lunar_str = event.get("ngay_am_lich", "25 tháng 10 năm Ất Tỵ")
    day_name = event.get("thu", "CHỦ NHẬT")

    # Domain / Tên miền trang web
    domain = (config.get("ten_mien") or config.get("domain") or "https://hoangnhatthuyhang.vercel.app").strip().rstrip("/")

    if is_root:
        canonical_url = f"{domain}/"
        og_url = f"{domain}/"
        doc_title = f"{le_title} - {cr_title} &amp; {cd_title}"
        og_title = f"{le_title} - {cr_short} & {cd_short}"
        og_desc = (
            f"Trân trọng kính mời quý khách tới dự bữa cơm thân mật chung vui cùng gia đình "
            f"chúng tôi vào lúc {time_short} ngày {date_str} tại {venue_name}"
        )
        custom_og = (config.get("anh_share_chung") or "").strip()
        if custom_og.startswith("http://") or custom_og.startswith("https://"):
            og_image_url = custom_og
        else:
            og_image_url = f"{domain}/images/og_share.jpg"
    elif side == "gai":
        canonical_url = f"{domain}/nhagai"
        og_url = f"{domain}/nhagai"
        og_desc = (
            f"Trân trọng kính mời quý khách tới dự bữa cơm thân mật chung vui cùng gia đình Nhà Gái "
            f"chúng tôi vào lúc {time_short} ngày {date_str} tại {venue_name}"
        )
        custom_og = (config.get("anh_share_gai") or config.get("anh_share_nhagai") or "").strip()
        if custom_og.startswith("http://") or custom_og.startswith("https://"):
            og_image_url = custom_og
        else:
            og_image_url = f"{domain}/images/og_nhagai.jpg"
    else:
        canonical_url = f"{domain}/nhatrai"
        og_url = f"{domain}/nhatrai"
        og_desc = (
            f"Trân trọng kính mời quý khách tới dự bữa cơm thân mật chung vui cùng gia đình Nhà Trai "
            f"chúng tôi vào lúc {time_short} ngày {date_str} tại {venue_name}"
        )
        custom_og = (config.get("anh_share_trai") or config.get("anh_share_nhatrai") or "").strip()
        if custom_og.startswith("http://") or custom_og.startswith("https://"):
            og_image_url = custom_og
        else:
            og_image_url = f"{domain}/images/og_nhatrai.jpg"

    # Xóa sạch các thẻ canonical, og:*, twitter:*, description cũ bất kể thứ tự thuộc tính
    html = re.sub(r'<link[^>]*rel=["\']canonical["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*property=["\']og:[^"\']+["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*content=["\'][^"\']*["\'][^>]*property=["\']og:[^"\']+["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*name=["\']twitter:[^"\']+["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*content=["\'][^"\']*["\'][^>]*name=["\']twitter:[^"\']+["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*name=["\']description["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*content=["\'][^"\']*["\'][^>]*name=["\']description["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*name=["\']msapplication-TileImage["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]*content=["\'][^"\']*["\'][^>]*name=["\']msapplication-TileImage["\'][^>]*>', '', html, flags=re.IGNORECASE)

    # Khởi tạo gói thẻ Open Graph + Twitter Card đạt chuẩn tối đa cho Zalo & Facebook / Messenger
    og_meta_tags = (
        f'<link rel="canonical" href="{canonical_url}"/>\n'
        f'<meta name="description" content="{og_desc}"/>\n'
        f'<meta property="og:type" content="website"/>\n'
        f'<meta property="og:url" content="{og_url}"/>\n'
        f'<meta property="og:title" content="{og_title}"/>\n'
        f'<meta property="og:description" content="{og_desc}"/>\n'
        f'<meta property="og:image" content="{og_image_url}"/>\n'
        f'<meta property="og:image:secure_url" content="{og_image_url}"/>\n'
        f'<meta property="og:image:type" content="image/jpeg"/>\n'
        f'<meta property="og:image:width" content="1200"/>\n'
        f'<meta property="og:image:height" content="630"/>\n'
        f'<meta property="og:image:alt" content="{og_title}"/>\n'
        f'<meta property="og:site_name" content="Thiệp Cưới Online - {cr_short} &amp; {cd_short}"/>\n'
        f'<meta name="twitter:card" content="summary_large_image"/>\n'
        f'<meta name="twitter:url" content="{og_url}"/>\n'
        f'<meta name="twitter:title" content="{og_title}"/>\n'
        f'<meta name="twitter:description" content="{og_desc}"/>\n'
        f'<meta name="twitter:image" content="{og_image_url}"/>\n'
        f'<meta name="msapplication-TileImage" content="{domain}/images/untitled-1-20250323102909-q2zbh.png"/>'
    )

    html = re.sub(r"<title>[^<]+</title>", f"<title>{doc_title}</title>\n{og_meta_tags}", html, count=1, flags=re.IGNORECASE)

    # 2. Text Replacements
    text_replacements = [
        # Ceremony title (LỄ THÀNH HÔN vs LỄ VU QUY)
        ("LỄ THÀNH HÔN", le_title),
        (
            "lễ thành hôn được tổ chứcvào lúc 17 giờ 30 phút",
            f"{le_title.lower()} được tổ chức vào lúc {time_long}",
        ),
        (
            "lễ thành hôn được tổ chức vào lúc 17 giờ 30 phút",
            f"{le_title.lower()} được tổ chức vào lúc {time_long}",
        ),

        # Names
        ("NGUYỄN THANH SƠN", cr_full),
        ("THANH SƠN", cr_short),
        ("Thanh Sơn", cr_title),
        ("NGUYỄN MAI ANH", cd_full),
        ("MAI ANH", cd_short),
        ("Mai Anh", cd_title),

        # Parents
        ("Ông. Nguyễn Văn Quỳnh", chu_re.get("bo", "Ông. Nguyễn Văn Quỳnh")),
        ("Bà. Nguyễn Thanh Hải", chu_re.get("me", "Bà. Nguyễn Thanh Hải")),
        ("Ông. Nguyễn Hữu Thu", co_dau.get("bo", "Ông. Nguyễn Hữu Thu")),
        ("Bà. Trịnh Thị Thủy", co_dau.get("me", "Bà. Trịnh Thị Thủy")),

        # Event Dates & Times (Save the date: ngày dương lịch theo từng tiệc)
        ("30.10.2025", event.get("ngay_save_date") or (date_str if side == "gai" else main_wedding_date)),
        ("10 tháng 09 năm Ất Tỵ", lunar_str),
        ("THỨ NĂM", day_name),
        ("17 giờ 30 phút", time_long),
        ("17:30", time_short),

        # Venue
        ("Aquaria Palace", venue_name),
    ]

    # Timeline event times (Đón khách, Lễ, Khai tiệc)
    tl_ev = event
    tl_don_khach = tl_ev.get("gio_don_khach", "16:00" if side == "gai" else "10:30")
    tl_le_gio = tl_ev.get("gio_ngan", "16:30" if side == "gai" else "11:00")
    tl_le_title = tl_ev.get("tieu_de_le", "LỄ VU QUY" if side == "gai" else "LỄ THÀNH HÔN")
    tl_khai_tiec = tl_ev.get("gio_khai_tiec", "17:00" if side == "gai" else "11:30")

    text_replacements.extend([
        ("17:00", tl_don_khach),
        ("17:45", tl_khai_tiec),
    ])

    # Specific month and year
    new_day = event.get("ngay")
    new_month = event.get("thang")
    new_year = event.get("nam")
    if new_month:
        text_replacements.append(("tháng 10", f"tháng {new_month}"))
        text_replacements.append(("Tháng 10", f"Tháng {new_month}"))
    if new_year:
        text_replacements.append(("năm 2025", f"năm {new_year}"))

    for target, repl in text_replacements:
        if target in html:
            html = html.replace(target, repl)

    # Timeline elements precision replacement
    html = re.sub(r'(id="HEADLINE213"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{tl_don_khach}\g<2>', html)
    html = re.sub(r'(id="HEADLINE216"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{tl_le_gio}\g<2>', html)
    html = re.sub(r'(id="HEADLINE218"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{tl_le_title}\g<2>', html)
    html = re.sub(r'(id="HEADLINE219"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{tl_khai_tiec}\g<2>', html)

    # 2.1 Ceremony and Address configuration
    dual_events_css = ""
    if side == "gai":
        import urllib.parse
        tiec_gai = config.get("tiec_nha_gai", {})

        venue_gai = tiec_gai.get("ten_dia_diem", "Tư gia Nhà Gái")
        addr_gai = tiec_gai.get("dia_chi", "")
        maps_vu_quy = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote((venue_gai + ' ' + addr_gai).strip())}"

        dual_events_html = f"""<div class="wedding-dual-container">
  <!-- KHỐI LỄ VU QUY (TƯ GIA NHÀ GÁI) -->
  <div class="wedding-event-card">
    <div class="wedding-top-decor">
      <img src="images/gedgvdf-20250323084817-ey8uu.png" alt="decor" class="wedding-decor-img"/>
    </div>
    <div class="wedding-ceremony-title">{tiec_gai.get('tieu_de_le', 'LỄ VU QUY')} ĐƯỢC TỔ CHỨC</div>
    <div class="wedding-ceremony-time">VÀO LÚC {tiec_gai.get('gio_to_chuc', '16 giờ 30 phút').upper()}</div>
    
    <div class="wedding-date-box">
      <div class="wedding-date-dayname">{tiec_gai.get('thu', 'THỨ BẢY')}</div>
      <div class="wedding-date-row">
        <div class="wedding-date-month">THÁNG {tiec_gai.get('thang', '10')}</div>
        <div class="wedding-date-num">{tiec_gai.get('ngay', '17')}</div>
        <div class="wedding-date-year">NĂM {tiec_gai.get('nam', '2026')}</div>
      </div>
      <div class="wedding-date-lunar">(Tức ngày {tiec_gai.get('ngay_am_lich', '8 tháng 9 năm Bính Ngọ')})</div>
    </div>

    <div class="wedding-rings-decor">
      <img src="images/gedgvdf-20250323085104-ib_ky.png" alt="rings" class="wedding-rings-img"/>
    </div>

    <div class="wedding-venue-title">{venue_gai}</div>
    <div class="wedding-venue-addr">Địa chỉ: {addr_gai}</div>
    
    <div class="wedding-btn-wrapper">
      <a href="{maps_vu_quy}" target="_blank" class="wedding-map-btn">
        <img src="images/gedgvdf-20250323084322-cpc_l.png" alt="pin" class="wedding-map-pin"/>
        <span>CHỈ ĐƯỜNG</span>
      </a>
    </div>
  </div>
</div>"""

        p1 = html.find('<div class="ladi-element" id="HEADLINE52">')
        p2 = html.find('</a>', html.find('id="GROUP10"')) + 4
        if p1 != -1 and p2 > p1:
            html = html[:p1] + dual_events_html + html[p2:]

        dual_events_css = """
/* Trang Nhà Gái: Chiều cao SECTION3 chuẩn và hiển thị khối Lễ Vu Quy */
#SECTION3 {
    height: 1740.2px !important;
}
#IMAGE7, #IMAGE8 {
    display: none !important;
}
.wedding-dual-container {
    position: absolute;
    top: 1160px;
    left: 0;
    width: 420px;
    box-sizing: border-box;
    padding: 0 12px;
    text-align: center;
    font-family: RUJHYXJhbWuZCNZWRpdWudHRm, 'EB Garamond', serif;
    color: rgb(63, 92, 132);
}
.wedding-event-card {
    width: 100%;
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.wedding-top-decor {
    width: 100%;
    display: flex;
    justify-content: center;
    margin-bottom: 0px;
}
.wedding-decor-img {
    width: 95px;
    height: 95px;
    object-fit: contain;
    display: block;
}
.wedding-ceremony-title {
    font-size: 21px;
    line-height: 1.35;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
}
.wedding-ceremony-time {
    font-size: 20px;
    line-height: 1.35;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
    margin-bottom: 14px;
}
.wedding-date-box {
    width: 290px;
    margin: 0 auto 12px;
}
.wedding-date-dayname {
    font-size: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.wedding-date-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    height: 52px;
}
.wedding-date-month, .wedding-date-year {
    font-size: 19px;
    text-transform: uppercase;
    border-top: 1px solid rgb(63, 92, 132);
    border-bottom: 1px solid rgb(63, 92, 132);
    padding: 4px 6px;
    line-height: 1.2;
    min-width: 82px;
    box-sizing: border-box;
}
.wedding-date-num {
    font-size: 48px;
    line-height: 1;
    font-weight: normal;
    min-width: 50px;
}
.wedding-date-lunar {
    font-size: 16px;
    margin-top: 8px;
    color: rgb(63, 92, 132);
}
.wedding-rings-decor {
    margin: 14px auto 10px;
    display: flex;
    justify-content: center;
}
.wedding-rings-img {
    width: 56px;
    height: 56px;
    object-fit: contain;
}
.wedding-venue-title {
    font-size: 21px;
    line-height: 1.35;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: bold;
    margin: 0 15px 8px;
}
.wedding-venue-addr {
    font-size: 15px;
    line-height: 1.45;
    margin: 0 20px 14px;
}
.wedding-btn-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 8px;
}
.wedding-map-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    text-decoration: none;
    color: rgb(63, 92, 132);
    font-size: 17px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 4px 14px;
    transition: opacity 0.2s ease;
}
.wedding-map-btn:hover {
    opacity: 0.8;
}
.wedding-map-pin {
    width: 20px;
    height: 20px;
    object-fit: contain;
}
"""
    else:
        # Address replacement (handles &nbsp; and line breaks in template)
        if venue_addr:
            html = re.sub(
                r'(id="HEADLINE59"[^>]*><p[^>]*>).*?(</p>)',
                rf'\g<1>Địa chỉ: {venue_addr}\g<2>',
                html,
                flags=re.DOTALL,
            )

        # Google Maps link update for "Chỉ đường" button (GROUP10)
        if venue_addr or venue_name:
            import urllib.parse
            maps_query = urllib.parse.quote(f"{venue_name} {venue_addr}".strip())
            html = re.sub(
                r'href="https://maps\.app\.goo\.gl/[^"]*"(\s+id="GROUP10")',
                rf'href="https://www.google.com/maps/search/?api=1&query={maps_query}"\1',
                html,
            )

        # Replace calendar day 30 under HEADLINE55
        if new_day:
            html = re.sub(r'(id="HEADLINE55"[^>]*><p[^>]*>)30(</p>)', rf'\g<1>{new_day}\g<2>', html)

    # Update Ladipage countdown timer timestamp
    try:
        import datetime
        c_year = int(new_year) if new_year else 2026
        c_month = int(new_month) if new_month else 10
        c_day = int(event.get("ngay", 17)) if side == "gai" else main_wedding_day
        c_hour = int(time_short.split(":")[0]) if ":" in time_short else (16 if side == "gai" else 11)
        c_min = int(time_short.split(":")[1]) if ":" in time_short else (30 if side == "gai" else 0)
        c_dt = datetime.datetime(c_year, c_month, c_day, c_hour, c_min, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=7)))
        c_ts = int(c_dt.timestamp() * 1000)
        html = re.sub(r'("COUNTDOWN1":\{[^}]*"bT":)\d+', rf'\g<1>{c_ts}', html)
    except Exception:
        pass

    # 3. Popup Mừng Cưới (Account info and QR)
    # HEADLINE207: "Chú rể" or "Cô dâu"
    html = re.sub(
        r'(id="HEADLINE207"[^>]*><h3[^>]*>)[^<]*(</h3>)',
        rf'\g<1>{popup_role}\g<2>',
        html
    )
    # HEADLINE208: Name of recipient
    html = re.sub(
        r'(id="HEADLINE208"[^>]*><h3[^>]*>)[^<]*(</h3>)',
        rf'\g<1>{chu_tai_khoan}\g<2>',
        html
    )
    # HEADLINE209: Bank name and account number
    if ten_ngan_hang and so_tai_khoan:
        formatted_stk = f"{ten_ngan_hang}<br/>{so_tai_khoan}"
    elif so_tai_khoan:
        formatted_stk = so_tai_khoan
    elif ten_ngan_hang:
        formatted_stk = ten_ngan_hang
    else:
        formatted_stk = ""

    if formatted_stk:
        html = re.sub(
            r'(id="HEADLINE209"[^>]*><h3[^>]*>).*?(</h3>)',
            rf'\g<1>{formatted_stk}\g<2>',
            html,
            flags=re.DOTALL
        )
    else:
        # Clear default demo bank info (BIDV) so empty info doesn't show demo numbers
        html = re.sub(
            r'(id="HEADLINE209"[^>]*><h3[^>]*>).*?(</h3>)',
            r'\g<1>\g<2>',
            html,
            flags=re.DOTALL
        )

    # QR image for popup
    if qr_file:
        dest_qr = f"custom_qr_{side}{os.path.splitext(qr_file)[1].lower()}"
        shutil.copyfile(qr_file, os.path.join(IMAGES_DIR, dest_qr))
        html = html.replace(QR_SLOT, f"images/{dest_qr}")

    # 4. Apply all custom photos (album & hero)
    for old_slot, new_slot in slot_mapping.items():
        html = html.replace(old_slot, new_slot)

    # 5. Dynamic Calendar Grid & Heart calculation for exact month/year/wedding day
    cal_year = int(new_year) if new_year else 2026
    cal_month = int(new_month) if new_month else 10
    cal_day = int(event.get("ngay", 17)) if side == "gai" else main_wedding_day
    calendar_rules = generate_calendar_css(cal_year, cal_month, cal_day)

    timeline_pos = config.get("can_chinh_anh_timeline", "center 95%")
    savedate_pos = config.get("can_chinh_anh_savedate", "center 20%")
    album1_pos = config.get("can_chinh_anh_album1", "50% 37%")
    thankyou_pos = config.get("can_chinh_anh_thankyou", "50% 65%")
    hero_pos = config.get("can_chinh_anh_hero", "48% 60%")
    hero_scale = config.get("scale_anh_hero", "106%")

    # 6. Mừng Cưới Button visibility
    gift_button_css = ""
    if hide_gift_button:
        gift_button_css = """
/* Hide Mừng Cưới button and adjust countdown spacing */
#GROUP24 {
    display: none !important;
}
#HEADLINE83 {
    top: 490px !important;
}
#COUNTDOWN1 {
    top: 585px !important;
}
#HEADLINE84, #HEADLINE85, #HEADLINE86 {
    top: 577px !important;
}
"""

    # 6b. Dresscode Color Palette: Trắng - Xanh lá nhạt - Pastel Blue - Kem
    dresscode_colors = config.get("mau_dresscode") or ["#FFFFFF", "#A8C5A8", "#AEC6CF", "rgb(242, 233, 216)"]
    c1 = dresscode_colors[0] if len(dresscode_colors) > 0 else "#FFFFFF"
    c2 = dresscode_colors[1] if len(dresscode_colors) > 1 else "#A8C5A8"
    c3 = dresscode_colors[2] if len(dresscode_colors) > 2 else "#AEC6CF"
    c4 = dresscode_colors[3] if len(dresscode_colors) > 3 else "rgb(242, 233, 216)"

    dresscode_css = f"""
/* Dresscode Color Palette: Trắng - Xanh lá nhạt - Xanh dương - Kem/Be */
#BOX37 > .ladi-box {{
    background-color: {c1} !important;
    box-shadow: rgba(0, 0, 0, 0.15) 0px 10px 15px -8px, rgba(0, 0, 0, 0.08) 0px 0px 0px 1px !important;
}}
#BOX39 > .ladi-box {{
    background-color: {c2} !important;
}}
#BOX40 > .ladi-box {{
    background-color: {c3} !important;
}}
#BOX41 > .ladi-box {{
    background-color: {c4} !important;
}}
"""

    # 7. Inject UI Fixes:
    #   - Hero banner: prevent bride's name from wrapping onto line 2 and clipping,
    #     and adjust ampersand size/position so it sits cleanly between groom and bride
    #   - Section 3: prevent groom and bride names from wrapping and colliding
    #   - Dynamic accurate calendar grid and heart surrounding the wedding date
    custom_ui_fixes = f"""
<style id="custom_ui_fixes" type="text/css">
/* Fix Hero Banner: Name clipping & spacing */
#HEADLINE3, #HEADLINE4 {{
    width: 380px !important;
    left: 20px !important;
}}
#HEADLINE3 > .ladi-headline, #HEADLINE4 > .ladi-headline {{
    font-size: 52px !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
}}
#HEADLINE4 {{
    top: 395px !important;
}}
#HEADLINE5 {{
    top: 450px !important;
    left: 135px !important;
    width: 80px !important;
}}
#HEADLINE5 > .ladi-headline {{
    font-size: 72px !important;
    line-height: 1 !important;
}}
#HEADLINE3 {{
    top: 530px !important;
}}

/* Fix Section 3: Match original Image 2 layout with spacious margins and authentic watermark */
#HEADLINE49, #HEADLINE50 {{
    width: 400px !important;
    left: 10px !important;
}}
#HEADLINE49 > .ladi-headline, #HEADLINE50 > .ladi-headline {{
    font-size: 50px !important;
    line-height: 1.25 !important;
    white-space: nowrap !important;
    letter-spacing: 1px !important;
    text-align: center !important;
}}
#HEADLINE50 {{
    top: 475px !important;
}}
#HEADLINE51 {{
    width: 170px !important;
    left: 125px !important;
    top: 485px !important;
}}
#HEADLINE51 > .ladi-headline {{
    font-family: "MUZUViWSVAtQVJDSVRUWUEtQkVHQVRSSSPVEY" !important;
    font-size: 130px !important;
    line-height: 1.2 !important;
    text-align: center !important;
    opacity: 0.4 !important;
    color: rgb(63, 92, 132) !important;
}}
#HEADLINE49 {{
    top: 605px !important;
}}

/* Venue name & address spacing: moderate 20px gap */
#HEADLINE58 {{
    width: 390px !important;
    left: 15px !important;
    top: 1545px !important;
}}
#HEADLINE58 > .ladi-headline {{
    font-size: 21px !important;
    line-height: 1.35 !important;
}}
#HEADLINE59 {{
    width: 390px !important;
    left: 15px !important;
    top: 1594px !important;
}}
#GROUP10 {{
    top: 1652px !important;
}}

/* Căn chỉnh vị trí ảnh Hero, Timeline, Save the date & Album đầu tiên cân đối */
#BOX1 > .ladi-box {{
    background-size: {hero_scale} !important;
    background-position: {hero_pos} !important;
}}
#BOX9 > .ladi-box {{
    background-position: {timeline_pos} !important;
}}
#BOX3 > .ladi-box {{
    background-position: {savedate_pos} !important;
}}
#BOX17 > .ladi-box {{
    background-position: {album1_pos} !important;
}}
#BOX26 > .ladi-box {{
    background-position: {thankyou_pos} !important;
}}


{gift_button_css}
{dresscode_css}
{dual_events_css}
/* Calendar grid and wedding date heart */
{calendar_rules}
</style>
"""
    html = html.replace("</head>", custom_ui_fixes + "\n</head>", 1)

    # 7. Background music replacement
    bg_music = config.get("nhac_nen", "media/bg_music.mp3").strip()
    html = html.replace("https://camcui.vn/bai99.mp3", bg_music)
    html = html.replace("media/bg_music.mp3", bg_music)

    # 8. Fix relative paths if this page is placed in a subfolder (e.g. nhatrai/ or nhagai/)
    if is_subfolder:
        # Prepend ../ to local asset paths
        html = html.replace('href="css/', 'href="../css/')
        html = html.replace('href="images/', 'href="../images/')
        html = html.replace('src="images/', 'src="../images/')
        html = html.replace('src="js/', 'src="../js/')
        html = html.replace('url(\'images/', 'url(\'../images/')
        html = html.replace('url(\'fonts/', 'url(\'../fonts/')
        html = html.replace('content="images/', 'content="../images/')
        html = html.replace('"media/', '"../media/')
        html = html.replace('\'media/', '\'../media/')

    # 8. Full Album External Link & Lightbox Modal
    full_album_link = config.get("link_full_album", "https://photos.app.goo.gl/Nm2Mkga4rxEYE3bp9").strip()
    html = html.replace("https://photos.app.goo.gl/WoHaX2xmn4QDxfRY9", full_album_link)
    html = html.replace("#full-album", full_album_link)
    if album_files:
        lightbox_markup = generate_wedding_lightbox(
            album_files,
            is_subfolder,
            album_folder_name=album_folder_name,
            title=f"{cr_short} &amp; {cd_short}"
        )
        html = html.replace("</body>", lightbox_markup + "\n</body>", 1)


    return html



def inject_smart_router(html: str) -> str:
    """
    Inject a smart client-side router in root index.html.
    Detects ?side=nhagai or ?side=nhatrai and smoothly redirects/switches.
    """
    router_script = """
<script type="text/javascript">
(function() {
    try {
        var p = new URLSearchParams(window.location.search);
        var s = (p.get('side') || p.get('party') || p.get('to') || '').toLowerCase();
        if (s === 'nhagai' || s === 'cd' || s === 'gai') {
            window.location.replace('nhagai/index.html');
        } else if (s === 'nhatrai' || s === 'cr' || s === 'trai') {
            window.location.replace('nhatrai/index.html');
        }
    } catch(e) {}
})();
</script>
"""
    return html.replace("<head>", "<head>" + router_script, 1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--reset", "-r", "reset"):
        reset_to_original()
        return

    if not os.path.exists(ORIGINAL_HTML):
        shutil.copyfile(INDEX_HTML, ORIGINAL_HTML)

    if not os.path.exists(CONFIG_FILE):
        console.print(f"[bold red]Lỗi:[/bold red] Không tìm thấy file cấu hình `{CONFIG_FILE}`!")
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    with open(ORIGINAL_HTML, "r", encoding="utf-8") as f:
        base_html = f.read()

    console.print(
        Panel.fit(
            "[bold cyan]TÙY BIẾN THIỆP CƯỚI TÁCH BIỆT NHÀ TRAI & NHÀ GÁI[/bold cyan]\n"
            "[italic dim]Xuất bản link riêng cho Zalo & Facebook hiển thị chuẩn xác 100%[/italic dim]",
            border_style="cyan",
        )
    )

    # Prepare custom photos & OG share banners (1200x630)
    album_dir, album_folder_name = get_album_dir(config)
    slot_mapping, num_replaced, album_files = prepare_custom_images(album_dir)
    generate_og_banners(config, CUSTOM_DIR, IMAGES_DIR)

    # 1. Render Nhà Trai page
    trai_html_sub = render_page(base_html, config, "trai", slot_mapping, is_subfolder=True, is_root=False, album_files=album_files, album_folder_name=album_folder_name)
    trai_html_root = render_page(base_html, config, "trai", slot_mapping, is_subfolder=False, is_root=False, album_files=album_files, album_folder_name=album_folder_name)

    os.makedirs(NHA_TRAI_DIR, exist_ok=True)
    with open(os.path.join(NHA_TRAI_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(trai_html_sub)
    with open(NHA_TRAI_HTML, "w", encoding="utf-8") as f:
        f.write(trai_html_root)

    # 2. Render Nhà Gái page
    gai_html_sub = render_page(base_html, config, "gai", slot_mapping, is_subfolder=True, is_root=False, album_files=album_files, album_folder_name=album_folder_name)
    gai_html_root = render_page(base_html, config, "gai", slot_mapping, is_subfolder=False, is_root=False, album_files=album_files, album_folder_name=album_folder_name)

    os.makedirs(NHA_GAI_DIR, exist_ok=True)
    with open(os.path.join(NHA_GAI_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(gai_html_sub)
    with open(NHA_GAI_HTML, "w", encoding="utf-8") as f:
        f.write(gai_html_root)

    # 3. Render Root index.html (is_root=True với Open Graph chung & bộ định tuyến thông minh)
    root_html_base = render_page(base_html, config, "trai", slot_mapping, is_subfolder=False, is_root=True, album_files=album_files, album_folder_name=album_folder_name)
    root_html = inject_smart_router(root_html_base)
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(root_html)

    # Output Summary Table
    trai_info = config.get("tiec_nha_trai", {})
    gai_info = config.get("tiec_nha_gai", {})
    domain = (config.get("ten_mien") or config.get("domain") or "https://hoangnhatthuyhang.vercel.app").strip().rstrip("/")

    console.print()
    table = Table(title="[bold green]XUẤT BẢN THIỆP CƯỚI & OPEN GRAPH THÀNH CÔNG[/bold green]", border_style="green")
    table.add_column("Đối tượng", style="cyan", width=16)
    table.add_column("Tiêu đề & Ngày giờ", style="white", width=22)
    table.add_column("Link Chia Sẻ (Zalo / FB)", style="bold yellow")
    table.add_column("Link Ảnh Preview (og:image)", style="dim cyan")

    table.add_row(
        "Nhà Trai (Chú rể)",
        f"{trai_info.get('tieu_de_le')}\n{trai_info.get('gio_ngan')} - {trai_info.get('ngay_duong_lich')}",
        f"{domain}/nhatrai\n[dim](local: /nhatrai/)[/dim]",
        f"{domain}/images/og_nhatrai.jpg"
    )

    table.add_row(
        "Nhà Gái (Cô dâu)",
        f"{gai_info.get('tieu_de_le')}\n{gai_info.get('gio_ngan')} - {gai_info.get('ngay_duong_lich')}",
        f"{domain}/nhagai\n[dim](local: /nhagai/)[/dim]",
        f"{domain}/images/og_nhagai.jpg"
    )

    table.add_row(
        "Trang Chủ (Chung)",
        "Tự điều hướng theo ?side=nhagai",
        f"{domain}/\n[dim](local: /)[/dim]",
        f"{domain}/images/og_share.jpg"
    )

    console.print(table)

    console.print(f"\n[green]✓[/green] Đã cập nhật [bold]{num_replaced}[/bold] khung ảnh cưới tự động.")
    console.print(f"[green]✓[/green] Thư mục album đang kích hoạt: [bold cyan]{album_folder_name}[/bold cyan] ({len(album_files)} ảnh).")
    console.print(f"[green]✓[/green] Đã tạo 3 ảnh banner Open Graph (1200x630) tỉ lệ vàng chuẩn cho Zalo & Messenger.")
    console.print(f"[green]✓[/green] Tên miền đang cấu hình: [bold underline]{domain}[/bold underline] (có thể đổi trong `custom_wedding/info.json`).\n")
    console.print("[dim]Để khôi phục lại mẫu gốc ban đầu: python3 apply_wedding.py --reset[/dim]\n")


if __name__ == "__main__":
    main()

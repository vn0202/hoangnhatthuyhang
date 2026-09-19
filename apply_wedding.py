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

# Subdirectories for dual sides
NHA_TRAI_DIR = os.path.join(SITE_DIR, "nhatrai")
NHA_GAI_DIR = os.path.join(SITE_DIR, "nhagai")
NHA_TRAI_HTML = os.path.join(SITE_DIR, "nhatrai.html")
NHA_GAI_HTML = os.path.join(SITE_DIR, "nhagai.html")

# Specific wedding photo slots in the template:
HERO_SLOT = "images/itsk2851a-20251006144830-optts.jpg"       # BOX1: Ảnh bìa lớn mở đầu thiệp
SAVEDATE_SLOT = "images/itsk2754a-20251006145138-jfgqu.jpg"   # BOX3: Ảnh Save the date / Quyết định bên nhau trọn đời
GROOM_SLOT = "images/itsk3191a-20251008053414-kpxv0.jpg"      # BOX5: Ảnh chân dung Chú rể
BRIDE_SLOT = "images/itsk3101a-20251006145418-uz8ay.jpg"      # BOX6: Ảnh chân dung Cô dâu
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


def prepare_custom_images() -> Tuple[Dict[str, str], int]:
    """
    Process custom images in custom_wedding/ and custom_wedding/album/.
    Returns a dictionary mapping old slot URLs -> new image URLs, and count of replaced slots.
    """
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

    # 6. Remaining slots: fill from album/
    album_photos = []
    if os.path.exists(ALBUM_DIR):
        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".JPG", ".JPEG", ".PNG", ".WEBP"}
        for f in sorted(os.listdir(ALBUM_DIR)):
            _, ext = os.path.splitext(f)
            if ext.lower() in valid_exts:
                album_photos.append(os.path.join(ALBUM_DIR, f))

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

    return slot_mapping, replaced_count


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


def render_page(
    base_html: str,
    config: dict,
    side: str,  # "trai" or "gai"
    slot_mapping: Dict[str, str],
    is_subfolder: bool = False,
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

    # Determine event details for this side
    # Determine event details and bank person for this side
    if side == "gai":
        event = config.get("tiec_nha_gai") or config.get("thoi_gian_va_dia_diem", {})
        person = co_dau
        side_label = "Nhà Gái"
        le_title = event.get("tieu_de_le", "LỄ VU QUY")
        doc_title = f"{le_title} - {cd_title} &amp; {cr_title}"
        og_title = f"{le_title} - Cô dâu {cd_short} & Chú rể {cr_short}"
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

    # 1. Update Title & Open Graph Meta Tags for perfect Zalo/Facebook display
    venue_name = event.get("ten_dia_diem", "Trống Đồng Palace")
    venue_addr = event.get("dia_chi", "")
    date_str = event.get("ngay_duong_lich", "15.12.2025")
    time_short = event.get("gio_ngan", "17:30")
    time_long = event.get("gio_to_chuc", "17 giờ 30 phút")
    lunar_str = event.get("ngay_am_lich", "25 tháng 10 năm Ất Tỵ")
    day_name = event.get("thu", "CHỦ NHẬT")

    og_desc = (
        f"Trân trọng kính mời quý khách tới dự bữa cơm thân mật chung vui cùng gia đình {side_label} "
        f"chúng tôi vào lúc {time_short} ngày {date_str} tại {venue_name}"
    )

    html = re.sub(r"<title>[^<]+</title>", f"<title>{doc_title}</title>", html)
    html = re.sub(r'content="[^"]*Thanh Sơn &amp; Mai Anh Wedding[^"]*"', f'content="{og_title}"', html)
    html = re.sub(
        r'<meta content="[^"]*" name="description"/>',
        f'<meta content="{og_desc}" name="description"/>',
        html
    )
    html = re.sub(
        r'<meta content="[^"]*" property="og:description"/>',
        f'<meta content="{og_desc}" property="og:description"/>',
        html
    )

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

        # Event Dates & Times
        ("30.10.2025", date_str),
        ("10 tháng 09 năm Ất Tỵ", lunar_str),
        ("THỨ NĂM", day_name),
        ("17 giờ 30 phút", time_long),
        ("17:30", time_short),

        # Venue
        ("Aquaria Palace", venue_name),
    ]

    # Timeline event times (Đón khách, Lễ, Khai tiệc)
    gio_don_khach = event.get("gio_don_khach", "10:30" if side == "trai" else "16:00")
    gio_khai_tiec = event.get("gio_khai_tiec", "11:30" if side == "trai" else "17:00")
    text_replacements.extend([
        ("17:00", gio_don_khach),
        ("17:45", gio_khai_tiec),
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
    html = re.sub(r'(id="HEADLINE213"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{gio_don_khach}\g<2>', html)
    html = re.sub(r'(id="HEADLINE216"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{time_short}\g<2>', html)
    html = re.sub(r'(id="HEADLINE218"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{le_title}\g<2>', html)
    html = re.sub(r'(id="HEADLINE219"[^>]*><p[^>]*>).*?(</p>)', rf'\g<1>{gio_khai_tiec}\g<2>', html)

    # 2.1 Ceremony and Address configuration
    dual_events_css = ""
    if side == "gai":
        # Put bride first on Nhà Gái (Thúy Hằng & Hoàng Nhật)
        html = re.sub(r'(id="HEADLINE4"[^>]*><h3[^>]*>)[^<]*(</h3>)', rf'\g<1>{cd_short}\g<2>', html)
        html = re.sub(r'(id="HEADLINE3"[^>]*><h3[^>]*>)[^<]*(</h3>)', rf'\g<1>{cr_short}\g<2>', html)
        html = re.sub(r'(id="HEADLINE50"[^>]*><p[^>]*>)[^<]*(</p>)', rf'\g<1>{cd_short}\g<2>', html)
        html = re.sub(r'(id="HEADLINE49"[^>]*><p[^>]*>)[^<]*(</p>)', rf'\g<1>{cr_short}\g<2>', html)

        import urllib.parse
        tiec_gai = config.get("tiec_nha_gai", {})
        tiec_trai = config.get("tiec_nha_trai", {})

        venue_gai = tiec_gai.get("ten_dia_diem", "Tư gia Nhà Gái")
        addr_gai = tiec_gai.get("dia_chi", "")
        maps_vu_quy = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote((venue_gai + ' ' + addr_gai).strip())}"

        venue_trai = tiec_trai.get("ten_dia_diem", "Sảnh 5 - Tiệc cưới Mipec Tây Sơn")
        addr_trai = tiec_trai.get("dia_chi", "229 Phố Tây Sơn, Kim Liên, Hà Nội")
        maps_thanh_hon = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote((venue_trai + ' ' + addr_trai).strip())}"

        dual_events_html = f"""<div class="wedding-dual-container">
  <!-- KHỐI 1: LỄ VU QUY (TƯ GIA NHÀ GÁI) -->
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

  <!-- PHÂN CÁCH TRANG TRỌNG -->
  <div class="wedding-dual-divider">
    <span class="wedding-div-line"></span>
    <span class="wedding-div-icon">❦</span>
    <span class="wedding-div-line"></span>
  </div>

  <!-- KHỐI 2: LỄ THÀNH HÔN (MIPEC TÂY SƠN) -->
  <div class="wedding-event-card">
    <div class="wedding-top-decor">
      <img src="images/gedgvdf-20250323084817-ey8uu.png" alt="decor" class="wedding-decor-img"/>
    </div>
    <div class="wedding-ceremony-title">{tiec_trai.get('tieu_de_le', 'LỄ THÀNH HÔN')} ĐƯỢC TỔ CHỨC</div>
    <div class="wedding-ceremony-time">VÀO LÚC {tiec_trai.get('gio_to_chuc', '11 giờ 00 phút').upper()}</div>
    
    <div class="wedding-date-box">
      <div class="wedding-date-dayname">{tiec_trai.get('thu', 'CHỦ NHẬT')}</div>
      <div class="wedding-date-row">
        <div class="wedding-date-month">THÁNG {tiec_trai.get('thang', '10')}</div>
        <div class="wedding-date-num">{tiec_trai.get('ngay', '18')}</div>
        <div class="wedding-date-year">NĂM {tiec_trai.get('nam', '2026')}</div>
      </div>
      <div class="wedding-date-lunar">(Tức ngày {tiec_trai.get('ngay_am_lich', '9 tháng 9 năm Bính Ngọ')})</div>
    </div>

    <div class="wedding-rings-decor">
      <img src="images/gedgvdf-20250323085104-ib_ky.png" alt="rings" class="wedding-rings-img"/>
    </div>

    <div class="wedding-venue-title">{venue_trai}</div>
    <div class="wedding-venue-addr">Địa chỉ: {addr_trai}</div>
    
    <div class="wedding-btn-wrapper">
      <a href="{maps_thanh_hon}" target="_blank" class="wedding-map-btn">
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
/* Trang Nhà Gái: Mở rộng SECTION3 và hiển thị cả 2 lễ */
#SECTION3 {
    height: 2270px !important;
}
#IMAGE7, #IMAGE8 {
    display: none !important;
}
#HEADLINE134 {
    border: 1px dashed rgb(63, 92, 132) !important;
    border-radius: 50% !important;
    width: 32px !important;
    height: 32px !important;
    line-height: 32px !important;
    text-align: center !important;
    box-sizing: border-box !important;
    margin-left: -5px !important;
    margin-top: -3px !important;
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
.wedding-dual-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    width: 290px;
    margin: 20px auto 25px;
    opacity: 0.45;
}
.wedding-div-line {
    flex: 1;
    height: 1px;
    background: rgb(63, 92, 132);
}
.wedding-div-icon {
    font-size: 18px;
    color: rgb(63, 92, 132);
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
        c_day = int(new_day) if new_day else (18 if side == "trai" else 17)
        c_hour = int(time_short.split(":")[0]) if ":" in time_short else (11 if side == "trai" else 16)
        c_min = int(time_short.split(":")[1]) if ":" in time_short else (0 if side == "trai" else 30)
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

    # Update og:image tag
    first_img = slot_mapping.get(HERO_SLOT, "images/itsk2851a-20251006144830-optts.jpg")
    html = re.sub(
        r'property="og:image"\s+content="[^"]+"',
        f'property="og:image" content="{first_img}"',
        html
    )

    # 5. Dynamic Calendar Grid & Heart calculation for exact month/year/wedding day
    cal_year = int(new_year) if new_year else 2026
    cal_month = int(new_month) if new_month else 10
    cal_day = int(new_day) if new_day else (18 if side == "trai" else 17)
    calendar_rules = generate_calendar_css(cal_year, cal_month, cal_day)

    timeline_pos = config.get("can_chinh_anh_timeline", "center 80%")
    savedate_pos = config.get("can_chinh_anh_savedate", "center 20%")

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

/* Căn chỉnh vị trí ảnh Timeline & Save the date cân đối */
#BOX9 > .ladi-box {{
    background-position: {timeline_pos} !important;
}}
#BOX3 > .ladi-box {{
    background-position: {savedate_pos} !important;
}}

{gift_button_css}
{dual_events_css}
/* Calendar grid and wedding date heart */
{calendar_rules}
</style>
"""
    html = html.replace("</head>", custom_ui_fixes + "\n</head>", 1)

    # 7. Fix relative paths if this page is placed in a subfolder (e.g. nhatrai/ or nhagai/)
    if is_subfolder:
        # Prepend ../ to local asset paths
        html = html.replace('href="css/', 'href="../css/')
        html = html.replace('href="images/', 'href="../images/')
        html = html.replace('src="images/', 'src="../images/')
        html = html.replace('src="js/', 'src="../js/')
        html = html.replace('url(\'images/', 'url(\'../images/')
        html = html.replace('url(\'fonts/', 'url(\'../fonts/')
        html = html.replace('content="images/', 'content="../images/')

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

    # Prepare custom photos
    slot_mapping, num_replaced = prepare_custom_images()

    # 1. Render Nhà Trai page
    trai_html_sub = render_page(base_html, config, "trai", slot_mapping, is_subfolder=True)
    trai_html_root = render_page(base_html, config, "trai", slot_mapping, is_subfolder=False)

    os.makedirs(NHA_TRAI_DIR, exist_ok=True)
    with open(os.path.join(NHA_TRAI_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(trai_html_sub)
    with open(NHA_TRAI_HTML, "w", encoding="utf-8") as f:
        f.write(trai_html_root)

    # 2. Render Nhà Gái page
    gai_html_sub = render_page(base_html, config, "gai", slot_mapping, is_subfolder=True)
    gai_html_root = render_page(base_html, config, "gai", slot_mapping, is_subfolder=False)

    os.makedirs(NHA_GAI_DIR, exist_ok=True)
    with open(os.path.join(NHA_GAI_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(gai_html_sub)
    with open(NHA_GAI_HTML, "w", encoding="utf-8") as f:
        f.write(gai_html_root)

    # 3. Render Root index.html (defaults to Nhà Trai with smart parameter router)
    root_html = inject_smart_router(trai_html_root)
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(root_html)

    # Output Summary Table
    trai_info = config.get("tiec_nha_trai", {})
    gai_info = config.get("tiec_nha_gai", {})

    console.print()
    table = Table(title="[bold green]XUẤT BẢN THIỆP CƯỚI 2 BÊN THÀNH CÔNG[/bold green]", border_style="green")
    table.add_column("Đối tượng", style="cyan", width=15)
    table.add_column("Tiêu đề lễ & Ngày giờ", style="white")
    table.add_column("Địa điểm tổ chức", style="dim")
    table.add_column("Đường dẫn (Link Share Zalo/FB)", style="bold yellow")

    table.add_row(
        "Nhà Trai (Chú rể)",
        f"{trai_info.get('tieu_de_le')}\n{trai_info.get('gio_ngan')} - {trai_info.get('ngay_duong_lich')}",
        f"{trai_info.get('ten_dia_diem')}\n{trai_info.get('dia_chi')}",
        "http://localhost:8000/nhatrai/\n(hoặc nhatrai.html)"
    )

    table.add_row(
        "Nhà Gái (Cô dâu)",
        f"{gai_info.get('tieu_de_le')}\n{gai_info.get('gio_ngan')} - {gai_info.get('ngay_duong_lich')}",
        f"{gai_info.get('ten_dia_diem')}\n{gai_info.get('dia_chi')}",
        "http://localhost:8000/nhagai/\n(hoặc nhagai.html)"
    )

    console.print(table)

    console.print(f"\n[green]✓[/green] Đã cập nhật [bold]{num_replaced}[/bold] khung ảnh tự động.")
    console.print(f"[green]✓[/green] Hỗ trợ cả link tham số: [bold underline]http://localhost:8000/?side=nhagai[/bold underline] và [bold underline]http://localhost:8000/?side=nhatrai[/bold underline]\n")
    console.print("[dim]Để khôi phục lại mẫu gốc ban đầu: python3 apply_wedding.py --reset[/dim]\n")


if __name__ == "__main__":
    main()

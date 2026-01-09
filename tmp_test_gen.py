from video.render import SmartVideoRenderer

sample_desc = '''Áo Thun Cổ Tròn Clean Fit - B Brand Form Gọn, Tôn Dáng.

*THÔNG TIN SẢN PHẨM

Tên sản phẩm: Áo Thun Cổ tròn Clean Fit B Brand

Màu sắc: Trắng / Đen / Be

Size: M / L

Kiểu dáng: Form Cleanfit cổ tròn - ôm nhẹ, tôn dáng, gọn gàng.

Chất liệu vải: Cotton 250gsm

Vải có độ co giãn nhẹ, mềm mịn, bề mặt mượt và đứng form tốt.

*HƯỚNG DẪN SỬ DỤNG & BẢO QUẢN

Lần giặt đầu chỉ nên xả nước lạnh, không dùng bột giặt.

#AoThunCleanFit #AoThun
'''

r = SmartVideoRenderer(script_generator=None, tts_provider=None, avatar_provider=None, motion_planner=None)
sent = r.generate_script_sentences('Áo Thun Cổ Tròn Clean Fit', sample_desc, '0')
print('Generated sentences:')
for s in sent:
    print('-', s)

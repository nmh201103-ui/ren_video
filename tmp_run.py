from processor.content import ContentProcessor
raw = 'Sample title\n\nDescription short. Nice fit.'
proc = ContentProcessor()
res = proc.process({'title':'T','description':raw,'image_urls':['a.jpg','b.jpg'],'price':'199000','platform':'shopee'})
print('Processed keys:', list(res.keys()) if res else 'None')
print('Description:', res.get('description') if res else 'None')
print('Image_data:', res.get('image_data') if res else 'None')

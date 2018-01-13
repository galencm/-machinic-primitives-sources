# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import lorem
import textwrap

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import attr
import roman
import itertools
import glob
import os
#TODO pyicu for page numbers
#TODO PRNG for text?

@attr.s
class Boook(object):
    title = attr.ib()
    sections = attr.ib(default=attr.Factory(list))
    output_directory = attr.ib(default=".")

    def generate(self):
        if not os.path.isdir(self.output_directory):
            os.mkdir(self.output_directory)
        blank((240,240,1),0,self.title,title=self.title,output_directory=self.output_directory)
        blank((255,255,255),1,self.title,output_directory=self.output_directory)
        page_image(2,self.title,title=self.title,text=None,output_directory=self.output_directory)
        blank((255,255,255),3,self.title,output_directory=self.output_directory)

        sequence= 4
        paged=1
        for section,pages,numeration in self.sections:
            print(section,sequence)
            location = itertools.cycle(['bottom_left','bottom_right'])
            
            if section == 'index':
                for page in range(1,pages+1):
                    #print(sequence)
                    if numeration == 'partial':
                        adjusted_page=page+3 #hardcoded for title & toc
                    else:
                        adjusted_page=page
                    page_image(sequence,self.title,page_num=adjusted_page,page_num_location='bottom_center',locale='roman_lower',split_width=75,paragraphs=16,sparsity=1,output_directory=self.output_directory)
                    sequence+=1
                if sequence % 2 == 0:
                    blank((255,255,255),sequence,self.title,output_directory=self.output_directory)
                    sequence+=1
            elif section == 'toc':
                toc_text=''
                start=1
                for s,p,n in self.sections:
                    toc_text+='{}          {}\n'.format(s,start)
                    if n == 'full':
                        start+=p

                print(">>",toc_text)
                print("-------")
                page_image(sequence,self.title,custom_text=toc_text,page_num=sequence,page_num_location='bottom_center',locale='roman_lower',split_width=75,paragraphs=16,sparsity=-1,output_directory=self.output_directory)
                sequence +=1

            else:
                for page in range(1,pages+1):
                    print(">>>>>>>>",sequence,section)
                    if page == pages:
                        page_image(sequence,self.title,page_num=paged,paragraphs=9,page_num_location=next(location),output_directory=self.output_directory)
                    elif page == 1:
                        page_image(sequence,self.title,page_num=paged,title=section,paragraphs=9,y_start='half',page_num_location='bottom_center',output_directory=self.output_directory)
                    else:
                        if paged % 2 == 0:
                            page_image(sequence,self.title,chapter_header=section,chapter_header_location='top_center',page_num=paged,page_num_location=next(location),output_directory=self.output_directory)
                        else:
                            page_image(sequence,self.title,chapter_header=self.title,chapter_header_location='top_center',page_num=paged,page_num_location=next(location),output_directory=self.output_directory)

                    sequence+=1
                    paged+=1

        if sequence % 2 == 0:
            blank((255,255,255),sequence,self.title,output_directory=self.output_directory)
            sequence+=1
            blank((255,255,255),sequence,self.title,output_directory=self.output_directory)
            sequence+=1

        blank((255,255,255),sequence,self.title,output_directory=self.output_directory)
        print("^^^",sequence)
        sequence+=1
        blank((240,240,1),sequence,self.title,output_directory=self.output_directory)


def blank(color,sequence,boook_name,title=None,output_directory=''):
    img = Image.new('RGB',(1728,2304),color)
    w, h = img.size
    if title:
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("DejaVuSansMono.ttf", 60)
        draw.text((w/2,h/3),str(title),font=font, fill=(15,15,15))

    img.save(os.path.join(output_directory,'{}{:>04d}.jpg'.format(boook_name,sequence)))
    img.close()


def page_image(sequence,boook_name,chapter_header=None,chapter_header_location=None,page_num=None,text=True,custom_text=None,title=None,split_width=95,page_num_location="top_left",paragraphs=19,y_start=None,locale=None,sparsity=0,output_directory=''):
    if y_start is None:
        y_start = 'default'

    img = Image.new('RGB',(1728,2304),(210,210,210))
    draw = ImageDraw.Draw(img)
    #font = ImageFont.truetype("DejaVuSerif-BoldItalic.ttf", 25)
    font = ImageFont.truetype("DejaVuSansMono.ttf", 25)
    if text is True and custom_text is None:
        pagetext= ''.join([lorem.paragraph() for _  in range(paragraphs)])
    elif custom_text is not None:
        pagetext = custom_text
        lines = pagetext.split("\n")
        print("custom text is ",lines)
    elif text is None and custom_text is None:
        pagetext=' '

    if custom_text is None:
        line_split = split_width
        lines = [pagetext[i:i+line_split] for i in range(0, len(pagetext), line_split)]

    if sparsity > 0:
        dense = 0
        for i,l in enumerate(lines):
            if dense == sparsity:
                lines[i] = ' '
                dense=0
            else:
                dense+=1


    #lines = textwrap.wrap(pagetext, width=90)
    draw = ImageDraw.Draw(img)
    w, h = img.size

    numeral_locations = {
    "top_left": (50,50),
    "top_center":(w/2,10),
    "top_right":(w-150,10),
    "center_left":(50,h/2),
    "center_top_third":(w/2,h/3),
    "center_center":(w/2,h/2),
    "center_right":(w-150,h/2),
    "bottom_left":(50,h-100),
    "bottom_center":(w/2,h-100),
    "bottom_right":(w-150,h-100)
    }

    start_positions = {
    'top_quarter':(h/2)+(h/4),
    'half':h/2,
    'bottom_quarter':h/4,
    'default':150
    }


    y_text = start_positions[y_start]#150
    for line in lines:
        if line:
            width, height = font.getsize(line)
            #draw.text(((w - width) / 2, y_text), line, font=font, fill=(15,15,15))
            draw.text((150, y_text), line, font=font, fill=(15,15,15))
            #draw.text((10,10), line, font=font, fill=(15,15,15))
            #print(line)
            y_text += height

    #for k,v in numeral_locations.items():
    #    draw.text(v,k,font=font, fill=(15,15,15))
    if page_num:
        if locale == 'roman_lower':
            page_num=roman.toRoman(page_num).lower()
            print(page_num)
        draw.text(numeral_locations[page_num_location],str(page_num),font=font, fill=(15,15,15))

    if chapter_header:
        draw.text(numeral_locations[chapter_header_location],str(chapter_header),font=font, fill=(15,15,15))


    if title:
        font = ImageFont.truetype("DejaVuSansMono.ttf", 50)

        draw.text(numeral_locations['center_top_third'],str(title),font=font, fill=(15,15,15))


    img.save(os.path.join(output_directory,'{}{:>04d}.jpg'.format(boook_name,sequence)))
    img.close()


#b = Boook('foo',[('index',5,'partial'),('bar',10,'full')])

#b = Boook([('index',2),('bar',10)])
#b.generate()

#partial roman numerals
#'front_material',20)
#front_cover
#back_cover


#1 chapter 1          |             <chapter name> 2

#1        <book name> | <chapter name>             2

# b = Boook('texxt',[('toc',1,'partial'),('index',5,'partial'),('bar',5,'full'),('baz',5,'full'),('zab',15,'full'),('zoom',15,'full')],output_directory="/tmp/foo")
# b.generate()



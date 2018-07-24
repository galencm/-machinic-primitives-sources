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
from collections import OrderedDict
import glob
import os
import csv
import time
from logzero import logger

#TODO pyicu for page numbers
#TODO PRNG for text?

@attr.s
class Boook(object):
    title = attr.ib()
    sections = attr.ib(default=attr.Factory(list))
    output_directory = attr.ib(default=".")
    manifest_formats = attr.ib(default=attr.Factory(set))
    manifest_name = attr.ib(default="title")
    verbose_output =  attr.ib(default=False)
    dry_run = attr.ib(default=False)

    def generate(self):
        if not os.path.isdir(self.output_directory):
            os.mkdir(self.output_directory)
        # create/clear files to log to
        # use a default manifest.format_type ?
        for file_format in self.manifest_formats:
            if self.manifest_name == "title":
                filename = "{}.{}".format(self.title, file_format)
            else:
                filename = "manifest.{}".format(self.title, file_format)
            open(filename, 'w').close()

        generated = []
        generated.append(blank((240,240,1),0,self.title,title=self.title,dry_run=self.dry_run,output_directory=self.output_directory))
        generated.append(blank((255,255,255),1,self.title,dry_run=self.dry_run,output_directory=self.output_directory))
        generated.append(page_image(2,self.title,title=self.title,text=None,dry_run=self.dry_run,output_directory=self.output_directory))
        generated.append(blank((255,255,255),3,self.title,dry_run=self.dry_run,output_directory=self.output_directory))

        sequence= 4
        paged=1
        for section,pages,numeration in self.sections:
            logger.info("section: {} sequence: {}".format(section,sequence))
            location = itertools.cycle(['bottom_left','bottom_right'])
            
            if section == 'index':
                for page in range(1,pages+1):
                    if numeration == 'partial':
                        adjusted_page=page+3 #hardcoded for title & toc
                    else:
                        adjusted_page=page
                    generated.append(page_image(sequence,self.title,page_num=adjusted_page,page_num_location='bottom_center',locale='roman_lower',split_width=75,paragraphs=16,sparsity=1,section=section, dry_run=self.dry_run, output_directory=self.output_directory))
                    sequence+=1
                if sequence % 2 == 0:
                    generated.append(blank((255,255,255),sequence,self.title,section=section, dry_run=self.dry_run, output_directory=self.output_directory))
                    sequence+=1
            elif section == 'toc':
                toc_text=''
                start=1
                for s,p,n in self.sections:
                    toc_text+='{}          {}\n'.format(s,start)
                    if n == 'full':
                        start+=p
                logger.info("toc contents: {}".format(toc_text))
                generated.append(page_image(sequence,self.title,custom_text=toc_text,page_num=sequence,page_num_location='bottom_center',locale='roman_lower',split_width=75,paragraphs=16,sparsity=-1,section=section, dry_run=self.dry_run, output_directory=self.output_directory))
                sequence +=1
            else:
                for page in range(1,pages+1):
                    logger.info("sequence: {} section: {}".format(sequence,section))
                    if page == pages:
                        generated.append(page_image(sequence,self.title,page_num=paged,paragraphs=9,page_num_location=next(location),section=section, dry_run=self.dry_run, output_directory=self.output_directory))
                    elif page == 1:
                        generated.append(page_image(sequence,self.title,page_num=paged,title=section,paragraphs=9,y_start='half',page_num_location='bottom_center',section=section, dry_run=self.dry_run, output_directory=self.output_directory))
                    else:
                        if paged % 2 == 0:
                            generated.append(page_image(sequence,self.title,chapter_header=section,chapter_header_location='top_center',page_num=paged,page_num_location=next(location),section=section, dry_run=self.dry_run, output_directory=self.output_directory))
                        else:
                            generated.append(page_image(sequence,self.title,chapter_header=self.title,chapter_header_location='top_center',page_num=paged,page_num_location=next(location),section=section, dry_run=self.dry_run, output_directory=self.output_directory))

                    sequence+=1
                    paged+=1

        if sequence % 2 == 0:
            generated.append(blank((255,255,255),sequence,self.title,section=section, dry_run=self.dry_run, output_directory=self.output_directory))
            sequence+=1
            generated.append(blank((255,255,255),sequence,self.title,section=section, dry_run=self.dry_run, output_directory=self.output_directory))
            sequence+=1

        generated.append(blank((255,255,255),sequence,self.title,section=section, dry_run=self.dry_run, output_directory=self.output_directory))
        sequence+=1
        generated.append(blank((240,240,1),sequence,self.title,section=section, dry_run=self.dry_run, output_directory=self.output_directory))

        generated_with_headers = []
        for line in generated:
            filename, created, sequence, section, chapter_header, page_num = line
            generated_with_headers.append(OrderedDict({"filename" : filename,
                                      "created" : created,
                                      "sequence" : sequence,
                                      "section" : section,
                                      "chapter_header" : chapter_header,
                                      "page_number" : page_num}))

        for file_format in self.manifest_formats:
            if file_format == "csv":
                if self.manifest_name == "title":
                    filename = "{}.{}".format(self.title, file_format)
                else:
                    filename = "manifest.{}".format(self.title, file_format)
                with open(filename, "w") as csvfile:
                    writer = csv.DictWriter(csvfile, generated_with_headers[0].keys())
                    writer.writeheader()
                    writer.writerows(generated_with_headers)

        if self.verbose_output:
            for line in generated:
                print(line)

def blank(color,sequence,boook_name,title=None,section=None,dry_run=False,output_directory=''):
    filename = '{}{:>04d}.jpg'.format(boook_name,sequence)
    created = time.time()
    if not dry_run:
        img = Image.new('RGB',(1728,2304),color)
        w, h = img.size
        if title:
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("DejaVuSansMono.ttf", 60)
            draw.text((w/2,h/3),str(title),font=font, fill=(15,15,15))

        img.save(os.path.join(output_directory, filename))
        img.close()
    return filename, created, sequence, section, None, None

def page_image(sequence,boook_name,chapter_header=None,chapter_header_location=None,page_num=None,text=True,custom_text=None,title=None,split_width=95,page_num_location="top_left",paragraphs=19,y_start=None,locale=None,sparsity=0,section=None,dry_run=False,output_directory=''):
    filename = '{}{:>04d}.jpg'.format(boook_name,sequence)
    created = time.time()
    if not dry_run:
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
            draw.text(numeral_locations[page_num_location],str(page_num),font=font, fill=(15,15,15))

        if chapter_header:
            draw.text(numeral_locations[chapter_header_location],str(chapter_header),font=font, fill=(15,15,15))

        if title:
            font = ImageFont.truetype("DejaVuSansMono.ttf", 50)

            draw.text(numeral_locations['center_top_third'],str(title),font=font, fill=(15,15,15))

        img.save(os.path.join(output_directory, filename))
        img.close()
    return filename, created, sequence, section, chapter_header, page_num
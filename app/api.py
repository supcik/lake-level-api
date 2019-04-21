"""
Copyright 2019 Jacques Supcik, HEIA-FR

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import asyncio
import datetime
import json
import pprint
import re

from pyppeteer import launch
from quart import Quart
from quart.logging import create_logger

app = Quart(__name__)
LOG = create_logger(app)


@app.route('/check')
async def check():
    """ Check if the service is running (to help Dokku) """
    return "OK\n"


def date_from_euro(txt):
    l = [int(i) for i in txt.split(".")]
    return datetime.date(l[2], l[1], l[0]).isoformat()


def msm(txt):
    m = re.search(r'(\d*(?:\.\d*)?) msm', txt)
    if m:
        return float(m.group(1))
    else:
        return None


async def main_table(page, url):
    result = dict()
    await page.goto(url)

    tr = await page.querySelector('table>thead>tr')
    th = await tr.querySelectorAllEval('th', '(nodes => nodes.map(n => n.innerText))')

    days = [date_from_euro(i) for i in th[2:4]]

    for i in await page.querySelectorAll('table>tbody>tr'):
        td = await i.querySelectorAllEval('td', '(nodes => nodes.map(n => n.innerText))')
        name = td[0]
        name = re.sub(r'\**$', '', name)
        levels = [msm(i) for i in td[2:4]]
        result[name] = {'max': msm(td[1]), 'level': dict(zip(days, levels))}

    return result


async def previsions(page, url):
    await page.goto(url)

    days = list()
    table = await page.querySelector('td.lac-jours table')
    for i in await table.querySelectorAll('tbody>tr'):
        td = await i.querySelectorAllEval('td', '(nodes => nodes.map(n => n.innerText))')
        days.append(date_from_euro(td[0]))

    nv_min = list()
    table = await page.querySelector('td.lac-nv-min table')
    for i in await table.querySelectorAll('tbody>tr'):
        td = await i.querySelectorAllEval('td', '(nodes => nodes.map(n => n.innerText))')
        nv_min.append(msm(td[0]))

    nv_max = list()
    table = await page.querySelector('td.lac-nv-max table')
    for i in await table.querySelectorAll('tbody>tr'):
        td = await i.querySelectorAllEval('td', '(nodes => nodes.map(n => n.innerText))')
        nv_max.append(msm(td[0]))

    pairs = list(zip(nv_min, nv_max))
    return dict(zip(days, pairs))


@app.route('/data')
async def data():
    browser = await launch(args=['--no-sandbox'])
    page = await browser.newPage()

    main_data = await main_table(
        page, 'https://www.groupe-e.ch/fr/univers-groupe-e/niveau-lacs'
    )
    main_data['La Gruyère']['forecast'] = await previsions(
        page, 'https://www.groupe-e.ch/fr/univers-groupe-e/niveau-lacs/gruyere'
    )
    main_data['Schiffenen']['forecast'] = await previsions(
        page, 'https://www.groupe-e.ch/fr/univers-groupe-e/niveau-lacs/schiffenen'
    )

    await browser.close()
    return json.dumps(main_data)

if __name__ == "__main__":
    app.run(debug=False)

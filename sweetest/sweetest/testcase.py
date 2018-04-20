from time import sleep
from os import path
from sweetest.log import logger
from sweetest.globals import g
from sweetest.elements import e
from sweetest.windows import w
from sweetest.locator import locating_elements, locating_data, locating_element
from sweetest.keywords import web, common, mobile, http
from sweetest.config import web_keywords, common_keywords, mobile_keywords, http_keywords
from sweetest.utility import replace_dict, replace


def elements_format(page, element):
    if not page:
        page = g.current_page

    if not element:
        return page, '', element

    if page in ('SNIPPET', '用例片段') or element in ('变量赋值',):
        return page, '', element

    custom, el = e.have(page, element)
    g.current_page = page
    return page, custom, el


def v_data(d):
    data = ''
    for k,v in d.items():
        data += k + '=' + v + ','
    return data[:-1]


class TestCase:
    def __init__(self, testcase):
        self.testcase = testcase
        self.snippet_steps = {}

    def run(self):
        logger.info('Run the TestCase: %s|%s' %
                    (self.testcase['id'], self.testcase['title']))
        self.testcase['result'] = 'Pass'
        self.testcase['report'] = ''
        if_result = ''

        for index, step in enumerate(self.testcase['steps']):
            # if 为否，不执行 then 语句
            if step['control'] == '>' and not if_result:
                step['score'] = '-'
                continue

            # if 为真，不执行 else 语句
            if step['control'] == '<' and if_result:
                step['score'] = '-'
                continue

            logger.info('Run the Step: %s|%s|%s' %
                        (step['no'], step['keyword'], step['element']))

            step['page'], step['custom'], step['element'] = elements_format(
                step['page'], step['element'])
            try:
                # 变量替换
                replace_dict(step['data'])
                replace_dict(step['expected'])

                step['element'] = replace(step['element'])

                step['vdata'] = v_data(step['data'])

                if g.platform.lower() in ('web',) and step['keyword'] in web_keywords:
                    # 判断页面是否已和窗口做了关联，如果没有，就关联当前窗口，如果已关联，则判断是否需要切换
                    w.switch_window(step['page'])
                    # 判断是否需要切换 frmae
                    w.switch_frame(step['custom'])

                    # 根据关键字调用关键字实现
                    getattr(web, step['keyword'].lower())(step)

                elif g.platform.lower() in ('ios', 'android') and step['keyword'] in mobile_keywords:
                    # 根据关键字调用关键字实现
                    getattr(mobile, step['keyword'].lower())(step)

                elif step['keyword'] in http_keywords:
                    # 根据关键字调用关键字实现
                    getattr(http, step['keyword'].lower())(step)

                elif step['keyword'].lower() == 'execute':
                    steps = getattr(common, step['keyword'].lower())(step)
                    self.snippet_steps[index+1]= steps

                else:
                    # 根据关键字调用关键字实现
                    getattr(common, step['keyword'].lower())(step)
                logger.info('Run the Step: %s|%s|%s is Pass' %
                            (step['no'], step['keyword'], step['element']))
                step['score'] = 'OK'

                # if 语句结果赋值
                if step['control'] == '^':
                    if_result = True

                # 操作后，等待0.2秒
                sleep(0.2)
            except Exception as exception:
                file_name = g.project_name + '-' + g.sheet_name + g.start_time + \
                    '#' + self.testcase['id'] + '-' + str(step['no']) + '.png'
                snapshot_file = path.join('snapshot', file_name)
                try:
                    g.driver.get_screenshot_as_file(snapshot_file)
                except:
                    logger.exception('*** save the screenshot is fail ***')
                logger.exception('Run the Step: %s|%s|%s is Failure' %
                                 (step['no'], step['keyword'], step['element']))
                step['score'] = 'NO'

                # if 语句结果赋值
                if step['control'] == '^':
                    if_result = False
                    continue

                self.testcase['result'] = 'Fail'
                self.testcase['report'] = 'step-%s|%s|%s: %s' % (
                    step['no'], step['keyword'], step['element'], exception)
                step['remark'] += str(exception)
                break

        steps = []
        i = 0
        for k in self.snippet_steps:
            steps = self.testcase['steps'][i:k] + self.snippet_steps[k]
            i = k
        steps += self.testcase['steps'][i:]
        self.testcase['steps'] = steps
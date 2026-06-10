import os
import json
import base64
import traceback
import sys
from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from services.museum_service import get_all_museums

load_dotenv()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['JSON_AS_ASCII'] = True
CORS(app)

AMAP_KEY = os.environ.get('AMAP_KEY', '')
AMAP_WEB_KEY = os.environ.get('AMAP_WEB_KEY', '')
APP_PORT = int(os.environ.get('PORT', 5000))
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_API_URL = 'https://api.deepseek.com/v1/chat/completions'

BAIDU_ASR_API_KEY = os.environ.get('BAIDU_ASR_API_KEY', '')
BAIDU_ASR_SECRET_KEY = os.environ.get('BAIDU_ASR_SECRET_KEY', '')
BAIDU_ASR_TOKEN = None
BAIDU_ASR_TOKEN_EXPIRY = 0

# Token 用量追踪
TOKEN_LIMIT = 20_000_000
TOKEN_USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'token_usage.json')


def _read_token_usage():
    """读取累计 token 用量"""
    try:
        with open(TOKEN_USAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('total_tokens', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def _add_token_usage(count):
    """累加 token 用量并持久化"""
    os.makedirs(os.path.dirname(TOKEN_USAGE_FILE), exist_ok=True)
    total = _read_token_usage() + count
    with open(TOKEN_USAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'total_tokens': total}, f)
    return total


def load_museums():
    return get_all_museums()


def build_museum_context(museums):
    """构建简洁的博物馆信息上下文，供AI使用"""
    lines = ["【南京博物馆数据库】（格式：名称|类型|区域|门票|预约方式|简介）"]
    for m in museums:
        name = m.get('name', '')
        cat = m.get('category', '')
        district = m.get('district', '')
        ticket = m.get('ticket_info', '')[:20]
        desc = (m.get('intro_short', '') or m.get('desc', ''))[:60]
        reserve = m.get('reserve_link', '暂无') or '暂无'
        if len(reserve) > 50:
            reserve = reserve[:50] + '...'
        lines.append(f"{name}|{cat}|{district}|{ticket}|{reserve}|{desc}")
    return '\n'.join(lines)


SYSTEM_PROMPT_BASE = """你是「博物金陵」的AI导览员，热情专业地为游客介绍南京的博物馆。
回答要求：
1. 简洁有趣，2-4句话为宜，适当使用emoji表情
2. 如果涉及具体博物馆，请用【】标注博物馆名称，例如【南京博物院】
3. 推荐博物馆时，要包含特色亮点、门票信息和预约方式
4. 如果用户想预约或查看某个博物馆，主动提醒可以使用下方的预约按钮
5. 回答结尾可以追问引导用户了解更多（例如：需要我帮您查看南京博物院的预约信息吗？）
6. 当用户询问位于南京市之外的博物馆信息时，主动提醒用户该博物馆不在南京市范围内，不提供详细信息
请严格基于下面提供的博物馆数据库来回答，不要编造不存在的信息。"""


@app.route('/api/museums', methods=['GET'])
def list_museums():
    museums = load_museums()
    return jsonify(museums)


@app.route('/api/amap-config')
def get_amap_config():
    return jsonify({
        'webKey': AMAP_WEB_KEY
    })


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat')
def chat():
    return render_template('chat.html')


@app.route('/museum/<int:museum_id>/collections')
def museum_collections(museum_id):
    """博物馆代表文物独立页面"""
    museums = load_museums()
    museum = next((m for m in museums if m.get('id') == museum_id), None)
    if not museum:
        return "博物馆不存在", 404
    return render_template('collections.html', museum=museum)


@app.route('/api/reserve-info', methods=['GET'])
def reserve_info():
    """获取所有有预约链接的博物馆信息"""
    museum_id = request.args.get('id', type=int)
    museums = load_museums()

    if museum_id:
        for m in museums:
            if m.get('id') == museum_id:
                return jsonify({
                    'name': m.get('name'),
                    'ticket_info': m.get('ticket_info'),
                    'open_time': m.get('open_time'),
                    'reserve_link': m.get('reserve_link'),
                    'website': m.get('website'),
                    'wechat': m.get('wechat'),
                    'phone': m.get('phone'),
                    'address': m.get('address'),
                })
        return jsonify({'error': '博物馆不存在'}), 404

    reserve_list = []
    for m in museums:
        link = m.get('reserve_link') or m.get('website')
        if link:
            reserve_list.append({
                'id': m.get('id'),
                'name': m.get('name'),
                'ticket_info': m.get('ticket_info'),
                'reserve_link': link,
                'wechat': m.get('wechat'),
                'phone': m.get('phone'),
            })
    return jsonify(reserve_list)


def _json_response(data, status=200):
    """安全地返回 JSON 响应，强制 ASCII 编码，绕过任何 latin-1 问题"""
    body = json.dumps(data, ensure_ascii=True, separators=(',', ':'))
    return Response(
        body,
        status=status,
        mimetype='application/json',
    )


@app.route('/api/ask', methods=['POST'])
def ask_ai():
    data = request.get_json()
    question = data.get('question', '')

    if not GROQ_API_KEY:
        return _json_response({
            "answer": "AI \u670d\u52a1\u672a\u914d\u7f6e\uff0c\u8bf7\u5728 .env \u4e2d\u8bbe\u7f6e\u6709\u6548\u7684 API \u5bc6\u94a5\u3002",
            "actions": []
        }, 500)

    if not question.strip():
        return _json_response({"answer": "\u8bf7\u8f93\u5165\u60a8\u7684\u95ee\u9898", "actions": []}, 400)

    if _read_token_usage() >= TOKEN_LIMIT:
        return _json_response({"answer": "AI \u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5", "actions": []}, 503)

    museums = load_museums()
    museum_context = build_museum_context(museums)

    system_prompt = SYSTEM_PROMPT_BASE + "\n\n" + museum_context

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    try:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        response = requests.post(GROQ_API_URL, headers=headers, data=body, timeout=30)
        result = json.loads(response.content)

        if 'usage' in result and 'total_tokens' in result['usage']:
            _add_token_usage(result['usage']['total_tokens'])

        if 'choices' in result and len(result['choices']) > 0:
            answer = result['choices'][0]['message']['content']
            actions = extract_museum_actions(answer, museums)
            return _json_response({"answer": answer, "actions": actions})
        else:
            return _json_response({"answer": f"AI \u8fd4\u56de\u683c\u5f0f\u5f02\u5e38: {json.dumps(result, ensure_ascii=True)}", "actions": []}, 500)

    except requests.exceptions.Timeout:
        return _json_response({"answer": "AI \u670d\u52a1\u54cd\u5e94\u8d85\u65f6\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5", "actions": []}, 504)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return _json_response({"answer": f"AI \u670d\u52a1\u51fa\u9519: {repr(e)}", "actions": []}, 500)


def extract_museum_actions(answer_text, museums):
    """从AI回复中提取【博物馆名称】，匹配数据库生成操作按钮"""
    matched = set()
    for m in museums:
        name = m.get('name', '')
        if name and name in answer_text:
            matched.add(name)

    actions = []
    added_names = set()
    for m in museums:
        name = m.get('name', '')
        if name not in matched and name not in added_names:
            for alias in m.get('alias', []):
                if alias and len(alias) >= 2 and alias in answer_text:
                    matched.add(name)
                    break
            if m.get('category') and m['category'] in answer_text:
                key_terms = m['category'].split('·')
                overlap = [t for t in key_terms if len(t) >= 2 and t in answer_text]
                if overlap:
                    matched.add(name)

    for m in museums:
        name = m.get('name', '')
        if name in matched and name not in added_names:
            added_names.add(name)
            action = {
                'museum_name': name,
                'museum_id': m.get('id'),
                'category': m.get('category'),
                'district': m.get('district'),
            }
            link = m.get('reserve_link') or m.get('website')
            if link:
                action['reserve_link'] = link
            if m.get('lat') and m.get('lng'):
                action['lat'] = m['lat']
                action['lng'] = m['lng']
            actions.append(action)

    return actions


def get_baidu_access_token():
    """获取百度ASR access_token，带缓存"""
    global BAIDU_ASR_TOKEN, BAIDU_ASR_TOKEN_EXPIRY
    import time
    now = time.time()
    if BAIDU_ASR_TOKEN and now < BAIDU_ASR_TOKEN_EXPIRY - 300:
        return BAIDU_ASR_TOKEN

    if not BAIDU_ASR_API_KEY or not BAIDU_ASR_SECRET_KEY:
        return None

    url = 'https://aip.baidubce.com/oauth/2.0/token'
    params = {
        'grant_type': 'client_credentials',
        'client_id': BAIDU_ASR_API_KEY,
        'client_secret': BAIDU_ASR_SECRET_KEY
    }
    try:
        resp = requests.post(url, params=params, timeout=10)
        data = resp.json()
        BAIDU_ASR_TOKEN = data.get('access_token')
        expires = data.get('expires_in', 2592000)
        BAIDU_ASR_TOKEN_EXPIRY = now + expires
        return BAIDU_ASR_TOKEN
    except Exception:
        return None


@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """语音识别接口：接收音频，返回文字"""
    if 'audio' not in request.files:
        return jsonify({'error': '请上传音频文件', 'text': ''}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if len(audio_data) < 100:
        return jsonify({'error': '录音太短，请重试', 'text': ''}), 400

    # 转 base64
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    token = get_baidu_access_token()
    if not token:
        return jsonify({'error': '语音识别服务未配置，请在.env中设置BAIDU_ASR_API_KEY和BAIDU_ASR_SECRET_KEY', 'text': ''}), 500

    url = 'https://vop.baidu.com/server_api'
    payload = {
        'format': 'wav',
        'rate': 16000,
        'channel': 1,
        'cuid': 'bwujinling',
        'token': token,
        'speech': audio_base64,
        'len': len(audio_data),
        'dev_pid': 1537,  # 普通话(支持简单的英文识别)
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()

        if result.get('err_no') == 0:
            text = ' '.join(result.get('result', []))
            return jsonify({'text': text, 'error': ''})
        else:
            err_msg = result.get('err_msg', '识别失败')
            return jsonify({'text': '', 'error': f'识别失败: {err_msg}'}), 200
    except requests.exceptions.Timeout:
        return jsonify({'text': '', 'error': '语音服务超时，请重试'}), 504
    except Exception as e:
        return jsonify({'text': '', 'error': f'语音服务异常: {str(e)}'}), 500


if __name__ == '__main__':
   app.run(host='0.0.0.0', use_reloader=False, port=APP_PORT)

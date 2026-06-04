import os
import json
import re
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from services.museum_service import get_all_museums

load_dotenv()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)

AMAP_KEY = os.environ.get('AMAP_KEY', '')
APP_PORT = int(os.environ.get('PORT', 5000))
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_API_URL = 'https://api.deepseek.com/v1/chat/completions'


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


@app.route('/api/ask', methods=['POST'])
def ask_ai():
    data = request.get_json()
    question = data.get('question', '')

    if not GROQ_API_KEY:
        return jsonify({
            "answer": "AI 服务未配置，请在 .env 中设置有效的 API 密钥。",
            "actions": []
        }), 500

    if not question.strip():
        return jsonify({"answer": "请输入您的问题", "actions": []}), 400

    museums = load_museums()
    museum_context = build_museum_context(museums)

    system_prompt = SYSTEM_PROMPT_BASE + "\n\n" + museum_context

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
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
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            answer = result['choices'][0]['message']['content']
            actions = extract_museum_actions(answer, museums)
            return jsonify({"answer": answer, "actions": actions})
        else:
            return jsonify({"answer": f"AI 返回格式异常: {result}", "actions": []}), 500

    except requests.exceptions.Timeout:
        return jsonify({"answer": "AI 服务响应超时，请稍后重试", "actions": []}), 504
    except Exception as e:
        return jsonify({"answer": f"AI 服务出错: {str(e)}", "actions": []}), 500


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


if __name__ == '__main__':
    app.run(use_reloader=False, port=APP_PORT)

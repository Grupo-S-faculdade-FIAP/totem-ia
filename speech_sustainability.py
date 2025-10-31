#!/usr/bin/env python3
"""
Speech Sustainability - Text-to-Speech para TOTEM IA
Gera conteúdo sobre sustentabilidade e reciclagem de tampinhas
Utiliza OpenAI LLM e Hugging Face Speech Synthesis
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import openai
from huggingface_hub import HfApi
import requests

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class SpeechSustainability:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.hf_token = os.getenv('HUGGINGFACE_TOKEN')
        
        if not self.openai_api_key:
            raise ValueError("❌ OPENAI_API_KEY não encontrada em .env")
        if not self.hf_token:
            raise ValueError("❌ HUGGINGFACE_TOKEN não encontrada em .env")
        
        # Configurar OpenAI
        openai.api_key = self.openai_api_key
        
        self.speech_output_dir = Path("static/audio")
        self.speech_output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ SpeechSustainability inicializado")

    def generate_sustainability_script(self):
        """
        Gera um script sobre sustentabilidade e reciclagem usando OpenAI
        """
        logger.info("🤖 Gerando script de sustentabilidade com OpenAI...")
        
        prompt = """
        Crie um texto breve e inspirador (máximo 150 palavras) sobre sustentabilidade 
        e reciclagem de tampinhas para um totem inteligente de coleta. 
        O texto deve:
        - Ser motivador e educativo
        - Destacar a importância da reciclagem
        - Mencionar o impacto positivo no meio ambiente
        - Ser adequado para ser lido em voz alta
        - Usar linguagem simples e acessível
        
        Retorne APENAS o texto, sem introduções ou explicações adicionais.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em sustentabilidade e educação ambiental."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            script = response.choices[0].message.content.strip()
            logger.info(f"✅ Script gerado com sucesso!")
            logger.info(f"📝 Conteúdo:\n{script}\n")
            
            return script
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar script com OpenAI: {e}")
            # Fallback
            return self.get_fallback_script()

    def get_fallback_script(self):
        """Script padrão em caso de erro com OpenAI"""
        return """
        Olá! Bem-vindo ao TOTEM IA, seu aliado na sustentabilidade!
        
        Você sabia que reciclar tampinhas faz uma enorme diferença? 
        Cada tampinha reciclada economiza energia e recursos naturais, 
        reduzindo o impacto no nosso planeta.
        
        Ao depositar suas tampinhas aqui, você está contribuindo para um 
        futuro mais sustentável e verde. Juntos, podemos fazer a diferença!
        
        Obrigado por reciclar com inteligência!
        """

    def synthesize_speech(self, text, output_filename="speech_sustainability.mp3"):
        """
        Sintetiza fala a partir do texto usando Hugging Face
        Utiliza o modelo de TTS do Hugging Face
        """
        logger.info("🎙️ Sintetizando fala com Hugging Face...")
        
        try:
            # URL da API de inference do Hugging Face
            # Usando o modelo "espnet/kan-bayashi_ljspeech_glow-tts"
            api_url = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_glow-tts"
            
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            payload = {
                "inputs": text
            }
            
            logger.info(f"   Enviando para síntese de fala...")
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                output_path = self.speech_output_dir / output_filename
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ Áudio sintetizado com sucesso!")
                logger.info(f"   Salvo em: {output_path}")
                
                return str(output_path)
                
            else:
                logger.error(f"❌ Erro na API do Hugging Face: {response.status_code}")
                logger.error(f"   Resposta: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao sintetizar fala: {e}")
            return None

    def synthesize_speech_gpt(self, text, output_filename="speech_sustainability.mp3"):
        """
        Alternativa: Utiliza OpenAI Text-to-Speech (se disponível)
        """
        logger.info("🎙️ Sintetizando fala com OpenAI TTS...")
        
        try:
            output_path = self.speech_output_dir / output_filename
            
            # Usar client de OpenAI para TTS
            with openai.Audio.create(
                model="tts-1",
                input=text,
                voice="alloy"  # Opções: alloy, echo, fable, onyx, nova, shimmer
            ) as response:
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ Áudio sintetizado com sucesso com OpenAI!")
                logger.info(f"   Salvo em: {output_path}")
                
                return str(output_path)
                
        except Exception as e:
            logger.error(f"❌ Erro ao sintetizar com OpenAI TTS: {e}")
            return None

    def run(self):
        """Executa pipeline completo: gerar script + sintetizar fala"""
        print("=" * 80)
        print("🌱 TOTEM IA - SPEECH SUSTAINABILITY")
        print("   Geração de conteúdo sobre sustentabilidade com IA")
        print("=" * 80)
        print()
        
        # 1. Gerar script com OpenAI
        script = self.generate_sustainability_script()
        
        # 2. Sintetizar fala com Hugging Face
        audio_path = self.synthesize_speech(script)
        
        # 3. Fallback para OpenAI TTS se Hugging Face falhar
        if not audio_path:
            logger.info("   Tentando OpenAI TTS como alternativa...")
            audio_path = self.synthesize_speech_gpt(script)
        
        print()
        if audio_path:
            print("✅ Pipeline concluído com sucesso!")
            print(f"   📄 Script gerado")
            print(f"   🎙️ Áudio sintetizado: {audio_path}")
        else:
            print("❌ Erro ao completar o pipeline")
        
        print("=" * 80)
        return audio_path

if __name__ == '__main__':
    try:
        speech = SpeechSustainability()
        audio_file = speech.run()
        
        if audio_file:
            print(f"\n✨ Arquivo de áudio disponível em: {audio_file}")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        import traceback
        traceback.print_exc()

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      body: "Use POST"
    }
  }

  const data = JSON.parse(event.body || "{}")

  console.log("Dados recebidos:", data)

  // limites que o Pico vai usar
  const resposta = {
    limite_min: 20,
    limite_max: 28,
    status: "OK"
  }

  return {
    statusCode: 200,
    body: JSON.stringify(resposta)
  }
}
